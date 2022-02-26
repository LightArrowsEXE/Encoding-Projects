from pathlib import Path
import os
from typing import Any, Dict, Iterable, Tuple, Union

import vapoursynth as vs
from lvsfunc.misc import source
from lvsfunc.types import Range
from vardautomation import FileInfo, PresetBD, PresetFLAC, VPath

from project_module import encoder as enc
from project_module import flt

core = vs.core


shader_file = 'assets/FSRCNNX_x2_56-16-4-1.glsl'
if not Path(shader_file).exists():
    hookpath = r"mpv/shaders/FSRCNNX_x2_56-16-4-1.glsl"
    shader_file = os.path.join(str(os.getenv("APPDATA")), hookpath)

use_cuda: bool = __name__ == '__main__'


# Sources
JP_BD = FileInfo(r'BDMV/[BDMV] Kobayashi-san Chi no Maid Dragon Vol.2/BDMV/STREAM/00006.m2ts', (None, -24),
                 idx=lambda x: source(x, cachedir=''), preset=[PresetBD, PresetFLAC])
JP_BD.name_file_final = VPath(fr"premux/{JP_BD.name} (Premux).mkv")
JP_BD.a_src_cut = VPath(JP_BD.name)
JP_BD.do_qpfile = True


# Scenefiltering
stronger_deblock_ranges: Iterable[Range] = [  # Heavy compression artefacting
    (1941, 1996)
]

zones: Dict[Tuple[int, int], Dict[str, Any]] = {  # Zones for x265
}


def filterchain() -> Union[vs.VideoNode, Tuple[vs.VideoNode, ...]]:
    """Main filterchain"""
    import lvsfunc as lvf
    import vardefunc as vdf
    import havsfunc as haf
    from ccd import ccd
    from vsutil import depth, get_y

    src = JP_BD.clip_cut
    src = depth(src, 16)
    src_y = get_y(src)

    # We wanna keep the denoising weak due to all the strong textures, but dark areas look so meh
    adap_mask = core.adg.Mask(src_y.std.PlaneStats(), 3.5).deblock.Deblock(24).dfttest.DFTTest(sigma=1.0)
    pre_dpir = lvf.deblock.vsdpir(src, strength=20, mode='deblock', matrix=1, cuda=use_cuda)
    pre_dft = core.dfttest.DFTTest(src, sigma=1.0)
    pre_den = core.std.MaskedMerge(pre_dft, pre_dpir, adap_mask)

    denoise_y = haf.SMDegrain(src, tr=3, thSAD=150, plane=0, pel=4, subpixel=3, blksize=8, chroma=False,
                              prefilter=pre_den, mfilter=pre_den)
    denoise = ccd(denoise_y, threshold=5, matrix='709')

    if stronger_deblock_ranges:  # But sometimes...
        # Just gonna have to pray the VRAM usage doesn't spike too hard and kills the encode lol
        deblock_str = lvf.deblock.vsdpir(denoise, strength=45, cuda=use_cuda, matrix=1)
        denoise = lvf.rfs(denoise, deblock_str, stronger_deblock_ranges)

    decs = vdf.noise.decsiz(denoise, sigmaS=8, min_in=208 << 8, max_in=232 << 8,
                            protect_mask=core.std.Prewitt(get_y(src), scale=0.5).std.Maximum())

    baa = lvf.aa.based_aa(decs, str(shader_file))
    sraa = lvf.sraa(decs, rfactor=1.70)
    clmp = lvf.aa.clamp_aa(decs, baa, sraa, strength=1.20)
    clmp = core.rgvs.Repair(clmp, decs, 13)

    deband = core.average.Mean([
        flt.masked_placebo(clmp, rad=6.5, thr=2.5, itr=2, grain=4),
        flt.masked_placebo(clmp, rad=6.5, thr=4.5, itr=2, grain=4),
        flt.zzdeband(clmp, denoised=True)
    ])

    grain = vdf.noise.Graigasm(
        thrs=[x << 8 for x in (32, 80, 128, 176)],
        strengths=[(0.25, 0.0), (0.20, 0.0), (0.15, 0.0), (0.0, 0.0)],
        sizes=(1.25, 1.20, 1.15, 1),
        sharps=(80, 70, 60, 50),
        grainers=[
            vdf.noise.AddGrain(seed=69420, constant=True),
            vdf.noise.AddGrain(seed=69420, constant=False),
            vdf.noise.AddGrain(seed=69420, constant=False)
        ]).graining(deband)

    final = flt.selector(src, grain)

    return final


if __name__ == '__main__':
    FILTERED = filterchain()
    enc.Encoder(JP_BD, FILTERED).run(clean_up=True)  # type: ignore
elif __name__ == '__vapoursynth__':
    FILTERED = filterchain()
    if not isinstance(FILTERED, vs.VideoNode):
        raise ImportError(f"Input clip has multiple output nodes ({len(FILTERED)})! Please output just 1 clip")
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
