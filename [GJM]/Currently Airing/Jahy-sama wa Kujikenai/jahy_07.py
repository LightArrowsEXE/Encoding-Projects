import argparse  # noqa
from typing import List, Tuple, Union

import vapoursynth as vs
from lvsfunc.misc import source
from lvsfunc.types import Range
from vardautomation import FileInfo, PresetAAC, PresetWEB, VPath

from project_module import encoder as enc
from project_module import flt  # noqa

core = vs.core

make_wraw: bool = False  # Create a workraw
enc_type = 'Premux' if not make_wraw else 'wraw'

EP_NUM = __file__[-5:-3]


# Sources
JP_clip = FileInfo(f'sources/{EP_NUM}/[NC-Raws] 迦希女王不会放弃！ - {EP_NUM} [B-Global][WEB-DL][1080p][AVC AAC][ENG_TH_SRT][MKV].mkv',
                   idx=lambda x: source(x, force_lsmas=True, cachedir=''),
                   preset=[PresetWEB, PresetAAC])
JP_clip.name_file_final = VPath(f"{enc_type.lower()}/Jahy_{EP_NUM} ({enc_type}).mkv")
JP_clip.name_clip_output = VPath(JP_clip.name + '.265')
JP_clip.do_qpfile = True

# Common variables
# OP/ED frames
opstart: Union[int, bool] = 960
edstart: Union[int, bool] = 30617

freeze_ranges: List[List[int]] = [  # [start_frame, end_frame, frame]
    [opstart, opstart+18, opstart],
    [opstart+87, opstart+96, opstart+87],
    [opstart+201, opstart+207, opstart],
    [opstart+238, opstart+244, opstart],
]

hardsub_sign: List[Range] = [  # Leftover hardsubbed signs that need a stronger mask
]

replace_scenes: List[Range] = [  # List of scenes to replace
]


def pre_freeze() -> vs.VideoNode:
    """Performing some freezeframing in the OP at the Typesetter's request"""
    from adjust import Tweak
    from vsutil import insert_clip

    src = JP_clip.clip_cut

    if opstart:
        freeze = core.std.FreezeFrames(
            src,
            [s[0] for s in freeze_ranges],
            [e[1] for e in freeze_ranges],
            [f[2] for f in freeze_ranges]
        )

        to_adjust = freeze[opstart+87]
        adjust = Tweak(to_adjust, hue=-18)
        adjust = adjust * (freeze_ranges[2][1] - freeze_ranges[2][0] + 1)
        insert = insert_clip(freeze, adjust, freeze_ranges[2][0])
    else:
        insert = src

    return insert


def filterchain() -> Union[vs.VideoNode, Tuple[vs.VideoNode, ...]]:
    """Regular VapourSynth filterchain"""
    import EoEfunc as eoe
    import havsfunc as haf
    import lvsfunc as lvf
    import vardefunc as vdf
    from adptvgrnMod import adptvgrnMod
    from ccd import ccd
    from muvsfunc import SSIM_downsample
    from vsutil import depth, get_y, iterate

    src = pre_freeze().std.AssumeFPS(fpsnum=24000, fpsden=1001)
    src = depth(src, 16)

    # TO-DO: Figure out how they post-sharpened it. Probably some form of unsharpening?
    src_y = depth(get_y(src), 32)
    descale = lvf.kernels.Bicubic(b=0, c=3/4).descale(src_y, 1440, 810)
    double = vdf.scale.nnedi3cl_double(descale, pscrn=1)
    rescale = depth(SSIM_downsample(double, 1920, 1080), 16)
    scaled = vdf.misc.merge_chroma(rescale, src)

    denoise = core.knlm.KNLMeansCL(scaled, d=1, a=3, s=4, h=0.4, channels='Y')
    stab = haf.GSMC(denoise, radius=2, planes=[0])
    cdenoise = ccd(stab, threshold=5, matrix='709')
    decs = vdf.noise.decsiz(cdenoise, sigmaS=4, min_in=208 << 8, max_in=232 << 8)

    dehalo = haf.YAHR(decs, blur=2, depth=32)
    halo_mask = lvf.mask.halo_mask(decs, rad=3, brz=0.3, thma=0.42)
    dehalo_masked = core.std.MaskedMerge(decs, dehalo, halo_mask)
    dehalo_min = core.std.Expr([dehalo_masked, decs], "x y min")

    aa = lvf.aa.nneedi3_clamp(dehalo_min, strength=1.5)
    # Some scenes have super strong aliasing that I really don't wanna scenefilter until BDs. Thanks, Silver Link!
    aa_strong = lvf.sraa(dehalo_min, rfactor=1.35)
    aa_spliced = lvf.rfs(aa, aa_strong, [])

    upscale = lvf.kernels.Bicubic(b=0, c=3/4).scale(descale, 1920, 1080)
    credit_mask = lvf.scale.descale_detail_mask(src_y, upscale, threshold=0.08)
    credit_mask = iterate(credit_mask, core.std.Deflate, 3)
    credit_mask = iterate(credit_mask, core.std.Inflate, 3)
    credit_mask = iterate(credit_mask, core.std.Maximum, 2)
    merge_credits = core.std.MaskedMerge(aa_spliced, src, depth(credit_mask, 16))

    deband = flt.masked_f3kdb(merge_credits, rad=18, thr=32, grain=[24, 0])
    grain: vs.VideoNode = adptvgrnMod(deband, seed=42069, strength=0.15, luma_scaling=10,
                                      size=1.25, sharp=80, static=True, grain_chroma=False)

    return grain


def wraw_filterchain() -> vs.VideoNode:
    """Workraw filterchain with minimal filtering"""
    from vardefunc.deband import dumb3kdb
    from vsutil import depth

    src: vs.VideoNode = pre_freeze()
    src = depth(src, 16)

    deband = dumb3kdb(src, radius=16, threshold=30, grain=16)
    grain: vs.VideoNode = core.grain.Add(deband, 0.15)

    return grain


if __name__ == '__main__':
    FILTERED = filterchain() if not make_wraw else wraw_filterchain()
    enc.Encoder(JP_clip, FILTERED).run(wraw=make_wraw, make_comp=False, clean_up=True, ep_num=EP_NUM)  # type: ignore
elif __name__ == '__vapoursynth__':
    FILTERED = filterchain()
    if not isinstance(FILTERED, vs.VideoNode):
        for i, CLIP_FILTERED in enumerate(FILTERED, start=1):
            CLIP_FILTERED.set_output(i)
    else:
        FILTERED.set_output(1)
else:
    JP_clip.clip_cut.set_output(0)
    # FILTERED = pre_freeze()
    FILTERED = filterchain() if not make_wraw else wraw_filterchain()
    if not isinstance(FILTERED, vs.VideoNode):
        for i, clip_filtered in enumerate(FILTERED, start=1):
            if clip_filtered:
                clip_filtered.set_output(i)
    else:
        FILTERED.set_output(1)
