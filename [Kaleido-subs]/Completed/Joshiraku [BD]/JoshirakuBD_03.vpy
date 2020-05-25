from functools import partial

import fvsfunc as fvf
import havsfunc as haf
import kagefunc as kgf
import xvs
from awsmfunc import bbmod
from cooldegrain import *
from vardefunc import diff_creditless_mask as DCM
from vsutil import get_y, join, split

import lvsfunc as lvf
import vapoursynth as vs

core = vs.core
core.max_cache_size = 1024 * 3


def descale(clip: vs.VideoNode) -> vs.VideoNode:
    planes    = split(clip)
    planes[0] = lvf.scale.descale(planes[0], **upscaled_args)
    planes[0] = core.resize.Bicubic(planes[0], 1280, 720)
    planes[1], planes[2] = [core.resize.Bicubic(p, planes[0].width, planes[0].height) for p in planes[1:]]
    return join(planes)


def warp(clip: vs.VideoNode) -> vs.VideoNode:
    l_mask = lvf.util.quick_resample(clip, kgf.retinex_edgemask)
    cwarp = core.std.MaskedMerge(xvs.WarpFixChromaBlend(scaled, depth=10), clip, l_mask)
    cwarp = core.rgsf.Repair(cwarp, clip, 13)

    return lvf.util.quick_resample(cwarp, partial(haf.FineDehalo, rx=2, darkstr=0, brightstr=1, contra=1))


def main_filter(clip: vs.VideoNode) -> vs.VideoNode:
    detail_mask = lvf.denoise.detail_mask(clip, pre_denoise = 1, brz_a = 0.06, brz_b = 0.04)
    denoise     = lvf.util.quick_resample(clip, partial(CoolDegrain, tr=1, thsad=48, thsadc=48, bits=16, blksize=8, overlap=4))
    deband      = core.placebo.Deband(denoise,  planes = 1,   grain = 4, **deband_args)
    deband      = core.placebo.Deband(deband,   planes = 2|4, grain = 0,  **deband_args)
    deband      = core.std.MaskedMerge(deband, clip, detail_mask)
    return kgf.adaptive_grain(deband, 0.1, luma_scaling=4)


# Arguments for repeated functions
deband_args   = dict(iterations = 2, threshold = 4, radius = 18)
upscaled_args = dict(height = 720, upscaler = None, kernel = lvf.kernels.Bicubic(0, 1/2))


# First OP & ED frames
opstart = 0
edstart = 31887


src = lvf.src(r"BDMV/JOSHIRAKU/121024_JOSHIRAKU_VOL2/BDMV/STREAM/00000.m2ts")
src = src[24:34789]

src_NCOP = lvf.src(r'BDMV/JOSHIRAKU/120926_JOSHIRAKU_VOL1/BDMV/STREAM/00001.m2ts')[24:-24].std.CropRel(2, 4)
src_NCED = lvf.src(r'BDMV/JOSHIRAKU/120926_JOSHIRAKU_VOL1/BDMV/STREAM/00002.m2ts')[24:-24].std.CropRel(2, 4)

# Looping some frames to make sure they match. Blanks added to make it easier to align with a stack_compare.
blank = core.std.BlankClip(src_NCOP)[0]
src_NCOP = src_NCOP+src_NCOP[-1]*9+blank
src_NCED = src_NCED+blank


src = core.std.CropRel(src, 2, 4)
ef = bbmod(src, 1, 1, 1, 2, thresh = 150, blur = 999, y = True, u = True, v = True)
ef = fvf.Depth(ef, 32)

scaled = descale(ef)
cwarp = warp(scaled)

credit_mask = core.std.Expr([DCM(src, src[opstart:opstart+src_NCOP.num_frames-1], src_NCOP[:-1], opstart, opstart+src_NCOP.num_frames-1),
                             DCM(src, src[edstart:edstart+src_NCED.num_frames-1], src_NCED[:-1], edstart, opstart+src_NCED.num_frames-1)],
                             expr = 'x y +')
credit_mask = core.resize.Spline36(credit_mask, 1280, 720, format=vs.GRAYS)
credit_mask = core.std.CropRel(credit_mask, left=4, right=4)
credit_mask = core.std.AddBorders(credit_mask, left=4, right=4)

downscale = core.resize.Spline36(ef, 1280, 720, format=cwarp.format)
merge = core.std.MaskedMerge(cwarp, downscale, credit_mask)

filtered = main_filter(merge)


out = filtered
final = fvf.Depth(out, 10)
final.set_output()
