import havsfunc as haf
import insaneAA as insaa
import kagefunc as kgf
import mvsfunc as mvf
from finedehalo import fine_dehalo
from vsutil import *

import lvsfunc as lvf
import vapoursynth as vs

core = vs.core


def interp(clip: vs.VideoNode, ranges = []) -> vs.VideoNode:
    l_mask = kgf.retinex_edgemask(clip)
    interp = haf.QTGMC(clip, InputType=1, TR0=2, TR1=2, TR2=1, Preset="Placebo", RepChroma=False)
    interp = core.std.MaskedMerge(clip, interp, l_mask)
    return lvf.rfs(clip, interp, ranges = ranges)


deband_args = dict(iterations = 1, threshold = 3, radius = 15)


aa_ranges     = [(1812, 1901), (1998, 2057), (2160, 2231), (2478, 2651)]
interp_ranges = [(1812, 1901), (2160, 2231), (2478, 2651)]


src = lvf.misc.source("00005.m2ts")
src = src[24:-24]
src = lvf.util.resampler(src, 16)


# Dealing with the poor lineart (thanks for helping out, DJATOM!)
sprsmpl = insaa.rescale(src, dx=1920, dy=1080, nnedi3_mode=2, pscrn=1, nsize=6)
aa = lvf.aa.nneedi3_clamp(src, strength=1.2)
aa = lvf.rfs(sprsmpl, aa, aa_ranges)

itrp = interp(aa, interp_ranges)
itrp = core.rgvs.Repair(itrp, aa, 13)

dehalo = fine_dehalo(itrp, rx=2.2, ry=2, darkstr=0, brightstr=0.6)


detail_mask = lvf.denoise.detail_mask(dehalo, pre_denoise = 0.75, brz_a = 0.04, brz_b = 0.065)
denoise = mvf.BM3D(dehalo, sigma=[0.8,0.6], profile1='lc')

deband = core.placebo.Deband(denoise, planes = 1,  grain = 4, **deband_args)
deband = core.placebo.Deband(deband, planes = 2|4, grain = 0, **deband_args)
deband = core.std.MaskedMerge(deband, dehalo, detail_mask)

grain = kgf.adaptive_grain(deband, 0.2, luma_scaling=6)


out = grain
final = lvf.util.resampler(out, 10)
final.set_output()
