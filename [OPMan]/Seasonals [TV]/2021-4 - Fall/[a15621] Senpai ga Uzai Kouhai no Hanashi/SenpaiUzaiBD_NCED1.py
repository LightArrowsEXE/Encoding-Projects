import os
from pathlib import Path
from typing import Any, Dict, Tuple, Union

import vapoursynth as vs
from lvsfunc.misc import source
from vardautomation import FileInfo, PresetBD, PresetFLAC, VPath

from project_module import encoder as enc
from project_module import flt

core = vs.core


shader_file = 'assets/FSRCNNX_x2_56-16-4-1.glsl'
if not Path(shader_file).exists():
    hookpath = r"mpv/shaders/FSRCNNX_x2_16-0-4-1.glsl"
    shader_file = os.path.join(str(os.getenv("APPDATA")), hookpath)


# Sources
JP_BD = FileInfo(r"BDMV/Senpai ga Uzai Kouhai no Hanashi Vol. 1 JP BDMV/KIZX_506/BDMV/STREAM/00003.m2ts", (2232, -24),
                 idx=lambda x: source(x, force_lsmas=True, cachedir=''), preset=[PresetBD, PresetFLAC])
JP_BD.name_file_final = VPath(fr"premux/{JP_BD.name} (Premux).mkv")
JP_BD.a_src_cut = JP_BD.name
JP_BD.do_qpfile = True


zones: Dict[Tuple[int, int], Dict[str, Any]] = {  # Zones for x265
}


def filterchain() -> Union[vs.VideoNode, Tuple[vs.VideoNode, ...]]:
    """Main VapourSynth filterchain"""
    import havsfunc as haf
    import lvsfunc as lvf
    import vardefunc as vdf
    from ccd import ccd
    from vsutil import depth

    src = JP_BD.clip_cut
    cloc = core.resize.Bicubic(src, chromaloc_in=2, chromaloc=0)
    src = depth(cloc, 16)

    halo_mask = lvf.mask.halo_mask(src, rad=1, brz=0.85, thmi=0.35, thma=0.95)
    halo_mask = halo_mask.std.Maximum().std.Inflate()

    bidehalo = lvf.dehalo.bidehalo(src, sigmaR=8/255, sigmaS=2.0, sigmaS_final=1.5)
    dehalo_den = core.dfttest.DFTTest(bidehalo, sigma=8.0)
    dehalo_clean = haf.EdgeCleaner(dehalo_den, strength=8, smode=1, hot=True)

    dehalo = core.std.MaskedMerge(src, dehalo_clean, halo_mask)

    # Certain cuts have a strong camera effect that amplifies haloing, and is likely intentional
    dehalo = lvf.rfs(dehalo, src, [(773, 786), (867, 886)])

    denoise = core.dfttest.DFTTest(dehalo, sigma=1.75)
    cdenoise = ccd(denoise, threshold=4, matrix='709')
    decs = vdf.noise.decsiz(cdenoise, sigmaS=8.0, min_in=208 << 8, max_in=232 << 8)

    baa = lvf.aa.based_aa(decs, str(shader_file))
    sraa = lvf.sraa(decs, rfactor=1.45)
    clmp = lvf.aa.clamp_aa(decs, baa, sraa, strength=1.45)

    darken = haf.FastLineDarkenMOD(clmp, strength=12)

    # Debanding and graining
    deband = flt.masked_f3kdb(darken, rad=18, thr=[24, 20])

    grain = vdf.noise.Graigasm(
        thrs=[x << 8 for x in (32, 80, 128, 176)],
        strengths=[(0.20, 0.0), (0.15, 0.0), (0.10, 0.0), (0.0, 0.0)],
        sizes=(1.20, 1.15, 1.10, 1),
        sharps=(70, 60, 50, 50),
        grainers=[
            vdf.noise.AddGrain(seed=69420, constant=True),
            vdf.noise.AddGrain(seed=69420, constant=True),
            vdf.noise.AddGrain(seed=69420, constant=True)
        ]).graining(deband)

    return grain


if __name__ == '__main__':
    FILTERED = filterchain()
    enc.Encoder(JP_BD, FILTERED).run(clean_up=True, zones=zones)  # type: ignore
elif __name__ == '__vapoursynth__':
    FILTERED = filterchain()
    if not isinstance(FILTERED, vs.VideoNode):
        raise ImportError(
            f"Input clip has multiple output nodes ({len(FILTERED)})! Please output just 1 clip"
        )
    else:
        enc.dither_down(FILTERED).set_output(0)
else:
    JP_BD.clip_cut.std.SetFrameProp('node', intval=0).set_output(0)
    FILTERED = filterchain()
    if not isinstance(FILTERED, vs.VideoNode):
        for i, clip_filtered in enumerate(FILTERED, start=1):
            clip_filtered.std.SetFrameProp('node', intval=i).set_output(i)
    else:
        FILTERED.std.SetFrameProp('node', intval=1).set_output(1)
