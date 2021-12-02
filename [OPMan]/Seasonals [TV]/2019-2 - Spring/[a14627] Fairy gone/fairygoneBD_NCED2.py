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
    hookpath = r"mpv/shaders/FSRCNNX_x2_56-16-4-1.glsl"
    shader_file = os.path.join(str(os.getenv("APPDATA")), hookpath)


# Sources
JP_BD = FileInfo(r"E:/src/[BDMV] Fairy gone/[BDMV][191218][TBR29115D][Fairy gone フェアリーゴーン Vol.5]/BDROM/BDMV/STREAM/00004.m2ts",
                 (24, -24),  idx=lambda x: source(x, force_lsmas=True, cachedir=''), preset=[PresetBD, PresetFLAC])
JP_BD.name_file_final = VPath(fr"premux/{JP_BD.name} (Premux).mkv")
JP_BD.a_src_cut = JP_BD.name
JP_BD.do_qpfile = True


zones: Dict[Tuple[int, int], Dict[str, Any]] = {  # Zones for x265
}


def filterchain() -> Union[vs.VideoNode, Tuple[vs.VideoNode, ...]]:
    """Main filterchain"""
    import lvsfunc as lvf
    import rekt
    import vardefunc as vdf
    from muvsfunc import SSIM_downsample
    from vsutil import depth, get_y

    src = JP_BD.clip_cut
    rkt = rekt.rektlvls(src, [0, -1], [15, 15], [0, -1], [15, 15])
    cloc = depth(rkt, 32).resize.Bicubic(chromaloc_in=1, chromaloc=0)

    descale = lvf.kernels.Bilinear().descale(get_y(cloc), 1280, 720)
    supersample = vdf.scale.nnedi3_upscale(descale)
    downscaled = SSIM_downsample(supersample, src.width, src.height, smooth=((3 ** 2 - 1) / 12) ** 0.5,
                                 sigmoid=True, filter_param_a=0, filter_param_b=0)
    scaled = vdf.misc.merge_chroma(downscaled, cloc)
    scaled = depth(scaled, 16)

    dft = core.dfttest.DFTTest(scaled, sigma=0.6, sbsize=8, sosize=6, tbsize=3, tosize=1)
    decs = vdf.noise.decsiz(dft, sigmaS=4, min_in=200 << 8, max_in=232 << 8)

    baa = lvf.aa.based_aa(decs, str(shader_file))
    sraa = lvf.sraa(decs, rfactor=1.5)
    clmp = lvf.aa.clamp_aa(decs, baa, sraa, strength=1.5)

    deband = flt.masked_f3kdb(clmp, rad=16, thr=[20, 16])

    grain = vdf.noise.Graigasm(
        thrs=[x << 8 for x in (32, 80, 128, 176)],
        strengths=[(0.25, 0.0), (0.20, 0.0), (0.15, 0.0), (0.0, 0.0)],
        sizes=(1.20, 1.15, 1.10, 1),
        sharps=(80, 70, 60, 50),
        grainers=[
            vdf.noise.AddGrain(seed=69420, constant=False),
            vdf.noise.AddGrain(seed=69420, constant=False),
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
