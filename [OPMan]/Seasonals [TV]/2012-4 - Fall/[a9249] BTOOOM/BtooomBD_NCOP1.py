from typing import Any, Dict, List, Tuple, Union

import vapoursynth as vs
from lvsfunc.misc import source
from lvsfunc.types import Range
from vardautomation import FileInfo, PresetBD, PresetFLAC, VPath

from project_module import encoder as enc
from project_module import flt

core = vs.core


# Sources
JP_BD = FileInfo(r'BDMV/Vol.01/BTOOOM 01/BDMV/STREAM/00010.m2ts', (24, None),
                 idx=lambda x: source(x, cachedir=''), preset=[PresetBD, PresetFLAC])
JP_BD.name_file_final = VPath(fr"premux/{JP_BD.name} (Premux).mkv")
JP_BD.a_src_cut = JP_BD.name
JP_BD.do_qpfile = True


shift_chr: List[Range] = [  # Shift chroma ranges
    (1007, 1112)
]

str_grain: List[Range] = [  # Super strong stylistic grain
    (264, 311), (556, 570), (616, 630), (992, 1006), (1288, 1301)
]

no_filter: List[Range] = [  # No filtering
    (2088, None)
]

zones: Dict[Tuple[int, int], Dict[str, Any]] = {  # Zones for x265
}


def filterchain() -> Union[vs.VideoNode, Tuple[vs.VideoNode, ...]]:
    """Main filterchain"""
    import lvsfunc as lvf
    import rekt
    import vardefunc as vdf
    from awsmfunc import bbmod
    from muvsfunc import SSIM_downsample
    from vsutil import depth, get_y

    src = JP_BD.clip_cut
    rkt = rekt.rektlvls(src, [0, -1], [17, 17], [0, -1], [17, 21])
    bb_y = bbmod(rkt, top=2, left=2, right=1, u=False, v=False)
    bb_uv = bbmod(bb_y, left=2, right=2, y=False)
    bb = depth(bb_uv, 32)

    descale = lvf.kernels.Mitchell().descale(get_y(bb), 1280, 720)
    up_chr = vdf.scale.to_444(bb, 1920, 1080, True).resize.Bicubic(1280, 720)
    descale_merge = vdf.misc.merge_chroma(descale, up_chr)
    denoise_down = lvf.deblock.vsdpir(descale_merge, strength=5, mode='deblock', matrix=1, i444=True, cuda=True)

    supersample = vdf.scale.nnedi3_upscale(get_y(denoise_down))
    downscaled = SSIM_downsample(supersample, bb.width, bb.height, smooth=((3 ** 2 - 1) / 12) ** 0.5,
                                 sigmoid=True, filter_param_a=0, filter_param_b=0)

    den_chr_up = core.resize.Bicubic(denoise_down, bb.width, bb.height, bb.format.id)
    den_chr_up_shift = core.resize.Bicubic(denoise_down, bb.width, bb.height, bb.format.id, src_left=-0.5)
    den_chr_up = lvf.rfs(den_chr_up, den_chr_up_shift, shift_chr)

    scaled = vdf.misc.merge_chroma(downscaled, den_chr_up)
    scaled = depth(scaled, 16)

    decs = vdf.noise.decsiz(scaled, sigmaS=4, min_in=208 << 8, max_in=232 << 8)

    deband = core.average.Mean([
        flt.masked_f3kdb(decs, rad=17, thr=[20, 24], grain=[24, 12]),
        flt.masked_f3kdb(decs, rad=21, thr=[32, 24], grain=[24, 12]),
        flt.masked_placebo(decs, rad=6, thr=2.8, itr=2, grain=4)
    ])

    grain = vdf.noise.Graigasm(
        thrs=[x << 8 for x in (32, 80, 128, 176)],
        strengths=[(0.25, 0.0), (0.20, 0.0), (0.15, 0.0), (0.0, 0.0)],
        sizes=(1.25, 1.20, 1.15, 1),
        sharps=(80, 70, 60, 50),
        grainers=[
            vdf.noise.AddGrain(seed=69420, constant=False),
            vdf.noise.AddGrain(seed=69420, constant=False),
            vdf.noise.AddGrain(seed=69420, constant=True)
        ]).graining(deband)

    grain_str = vdf.noise.Graigasm(
        thrs=[x << 8 for x in (32, 80, 128, 176)],
        strengths=[(0.35, 0.0), (0.30, 0.0), (0.25, 0.0), (0.0, 0.0)],
        sizes=(1.25, 1.20, 1.15, 1),
        sharps=(80, 70, 60, 50),
        grainers=[
            vdf.noise.AddGrain(seed=69420, constant=False),
            vdf.noise.AddGrain(seed=69420, constant=False),
            vdf.noise.AddGrain(seed=69420, constant=True)
        ]).graining(deband)

    grain = lvf.rfs(grain, grain_str, str_grain)

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
