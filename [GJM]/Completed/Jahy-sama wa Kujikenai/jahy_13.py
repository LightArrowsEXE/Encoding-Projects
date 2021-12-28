import os
from pathlib import Path
from typing import Tuple, Union

import vapoursynth as vs
from lvsfunc.misc import source
from vardautomation import FileInfo, PresetAAC, PresetWEB, VPath

from project_module import encoder as enc
from project_module import flt  # noqa

core = vs.core

make_wraw: bool = False  # Create a workraw
enc_type = 'Premux' if not make_wraw else 'wraw'

EP_NUM = __file__[-5:-3]


shader_file = 'assets/FSRCNNX_x2_56-16-4-1.glsl'
if not Path(shader_file).exists():
    hookpath = r"mpv/shaders/FSRCNNX_x2_56-16-4-1.glsl"
    shader_file = os.path.join(str(os.getenv("APPDATA")), hookpath)


# Sources
JP_clip = FileInfo(f'sources/{EP_NUM}/[NC-Raws] 迦希女王不会放弃！ - {EP_NUM} [B-Global][WEB-DL][1080p][AVC AAC][Multiple Subtitle][MKV].mkv',
                   idx=lambda x: source(x, force_lsmas=True, cachedir=''),
                   preset=[PresetWEB, PresetAAC])
JP_clip.name_file_final = VPath(f"{enc_type.lower()}/Jahy_{EP_NUM} ({enc_type}).mkv")
JP_clip.name_clip_output = VPath(JP_clip.name + '.265')
JP_clip.do_qpfile = True


def filterchain() -> Union[vs.VideoNode, Tuple[vs.VideoNode, ...]]:
    """Regular VapourSynth filterchain"""
    import EoEfunc.denoise as eoe
    import havsfunc as haf
    import lvsfunc as lvf
    import vardefunc as vdf
    from adptvgrnMod import adptvgrnMod
    from ccd import ccd
    from muvsfunc import SSIM_downsample
    from vsutil import depth, get_y, iterate
    from xvs import WarpFixChromaBlend

    src = JP_clip.clip_cut.std.AssumeFPS(fpsnum=24000, fpsden=1001)
    src = depth(src, 16)

    # TO-DO: Figure out how they post-sharpened it. Probably some form of unsharpening?
    src_y = depth(get_y(src), 32)
    descale = lvf.kernels.Bicubic(b=0, c=3/4).descale(src_y, 1440, 810)
    double = vdf.scale.nnedi3cl_double(descale, pscrn=1)
    rescale = depth(SSIM_downsample(double, 1920, 1080), 16)
    scaled = vdf.misc.merge_chroma(rescale, src)

    denoise_ref = core.dfttest.DFTTest(scaled, sigma=1.8)
    denoise = lvf.denoise.bm3d(scaled, sigma=[0.75, 0.65], ref=denoise_ref)
    cdenoise = ccd(denoise, threshold=3, matrix='709')
    decs = vdf.noise.decsiz(cdenoise, sigmaS=4, min_in=208 << 8, max_in=232 << 8)

    # Dehalo fuckery. Fuck the sharpening, dude
    dehalo = haf.YAHR(decs, blur=2, depth=32)
    dehalo_2 = lvf.dehalo.masked_dha(dehalo, ry=2.5, rx=2.5)
    halo_mask = lvf.mask.halo_mask(decs, rad=3, brz=0.3, thma=0.42)
    dehalo_masked = core.std.MaskedMerge(decs, dehalo_2, halo_mask)
    dehalo_min = core.std.Expr([dehalo_masked, decs], "x y min")

    # Brightening the lines to undo the unsharpening's line darkening
    bright = haf.FastLineDarkenMOD(dehalo_min, strength=-24)

    # AA
    baa = lvf.aa.based_aa(bright, str(shader_file))
    sraa = lvf.sraa(bright, rfactor=1.45)
    clmp = lvf.aa.clamp_aa(bright, baa, sraa, strength=1.45)

    line_mask = core.std.Prewitt(clmp)
    cwarp = WarpFixChromaBlend(clmp, thresh=96, depth=6)
    cwarp = core.std.MaskedMerge(cwarp, clmp, line_mask)

    upscale = lvf.kernels.Bicubic(b=0, c=3/4).scale(descale, 1920, 1080)
    credit_mask = lvf.scale.descale_detail_mask(src_y, upscale, threshold=0.08)
    credit_mask = iterate(credit_mask, core.std.Deflate, 3)
    credit_mask = iterate(credit_mask, core.std.Inflate, 3)
    credit_mask = iterate(credit_mask, core.std.Maximum, 2)
    merge_credits = core.std.MaskedMerge(cwarp, src, depth(credit_mask, 16))

    deband = flt.masked_f3kdb(merge_credits, rad=15, thr=20, grain=[12, 0])
    grain: vs.VideoNode = adptvgrnMod(deband, seed=42069, strength=0.15, luma_scaling=10,
                                      size=1.25, sharp=70, static=True, grain_chroma=False)

    return grain


def wraw_filterchain() -> vs.VideoNode:
    """Workraw filterchain with minimal filtering"""
    from debandshit.debanders import dumb3kdb
    from vsutil import depth

    src: vs.VideoNode = JP_clip.cut
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
