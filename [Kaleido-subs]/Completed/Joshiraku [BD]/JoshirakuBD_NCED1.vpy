from functools import partial

import fvsfunc as fvf
import havsfunc as haf
import kagefunc as kgf
import xvs
from awsmfunc import bbmod
from cooldegrain import *
from vsutil import join, split

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
deband_args     = dict(iterations = 2, threshold = 4, radius = 18)
upscaled_args   = dict(height = 720, upscaler = None, kernel = lvf.kernels.Bicubic(0, 1/2))


src = lvf.src(r"BDMV/JOSHIRAKU/120926_JOSHIRAKU_VOL1/BDMV/STREAM/00002.m2ts")[24:-24]
src = core.std.CropRel(src, 2, 4)
ef = bbmod(src, 1, 1, 3, 6, thresh = 40, blur = 999, y = True, u = False, v = False)
ef = fvf.Depth(ef, 32)

scaled = descale(ef)
cwarp = warp(scaled)
filtered = main_filter(cwarp)


out = filtered
final = fvf.Depth(out, 10)
final.set_output()
