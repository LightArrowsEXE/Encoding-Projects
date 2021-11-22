from typing import Any, Dict, List, Tuple, Union

import vapoursynth as vs
from lvsfunc.misc import source
from lvsfunc.types import Range
from vardautomation import FileInfo, PresetBD, PresetFLAC, VPath

from project_module import encoder as enc
from project_module import flt

core = vs.core


# Sources
JP_BD = FileInfo(r'BDMV/Deadman Wonderland/EXTRAS/OP (TV Cut Version).mkv', (12, -36),
                 idx=lambda x: source(x, force_lsmas=True, cachedir=''), preset=[PresetBD, PresetFLAC])
JP_BD.name_file_final = VPath(fr"premux/{JP_BD.name} (Premux).mkv")
JP_BD.a_src_cut = JP_BD.name
JP_BD.do_qpfile = True


no_filter: List[Range] = [  # No filtering on these ranges
    (None, 13), (2142, None)
]

zones: Dict[Tuple[int, int], Dict[str, Any]] = {  # Zones for x265
}


def filterchain() -> Union[vs.VideoNode, Tuple[vs.VideoNode, ...]]:
    """Main filterchain"""
    import lvsfunc as lvf
    import rekt
    import vardefunc as vdf
    from awsmfunc import bbmod
    from ccd import ccd
    from muvsfunc import SSIM_downsample
    from vsutil import depth, get_y

    src = JP_BD.clip_cut
    rkt = rekt.rektlvls(src, [0, -1], [30, 17], [0], [17])
    bb_y = bbmod(rkt, top=2, left=2, right=2, bottom=2, u=False, v=False, blur=9999)
    bb_uv = bbmod(bb_y, left=2, right=2, y=False)
    bb = depth(bb_uv, 32)

    descale = lvf.kernels.Spline36().descale(get_y(bb), 1280, 720)
    up_chr = vdf.scale.to_444(bb, 1920, 1080, True).resize.Bicubic(1280, 720)
    descale_merge = vdf.misc.merge_chroma(descale, up_chr)
    denoise_down = lvf.deblock.vsdpir(descale_merge, strength=0.5, mode='deblock', matrix=1, i444=True, cuda=True)

    supersample = vdf.scale.nnedi3_upscale(get_y(denoise_down))
    downscaled = SSIM_downsample(supersample, bb.width, bb.height, smooth=((3 ** 2 - 1) / 12) ** 0.5,
                                 sigmoid=True, filter_param_a=0, filter_param_b=0)

    scaled = vdf.misc.merge_chroma(downscaled, bb)
    scaled = depth(scaled, 16)

    den_uv = ccd(scaled, matrix='709')
    decs = vdf.noise.decsiz(den_uv, sigmaS=8, min_in=200 << 8, max_in=232 << 8)

    nn_aa = lvf.aa.nnedi3(opencl=True, dh=False)(decs)
    sraa = lvf.sraa(decs, rfactor=1.75)
    clmp = lvf.aa.clamp_aa(decs, nn_aa, sraa)

    dehalo = lvf.dehalo.masked_dha(clmp, brightstr=0.65)

    deband = flt.masked_f3kdb(dehalo, rad=17, thr=[24, 16], grain=[24, 12])

    grain = vdf.noise.Graigasm(
        thrs=[x << 8 for x in (32, 80, 128, 176)],
        strengths=[(0.20, 0.0), (0.15, 0.0), (0.10, 0.0), (0.0, 0.0)],
        sizes=(1.20, 1.15, 1.10, 1),
        sharps=(100, 80, 60, 20),
        grainers=[
            vdf.noise.AddGrain(seed=69420, constant=False),
            vdf.noise.AddGrain(seed=69420, constant=False),
            vdf.noise.AddGrain(seed=69420, constant=True)
        ]).graining(deband)

    no_flt = lvf.rfs(grain, depth(bb, 16), no_filter)

    return no_flt


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
