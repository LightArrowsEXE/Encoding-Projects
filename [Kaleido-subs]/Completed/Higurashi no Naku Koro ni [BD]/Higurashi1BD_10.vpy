import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import havsfunc as haf
import mvsfunc as mvf
import functools
from vsutil import *
from nnedi3_rpow2 import *
core = vs.core

opstart = 720


src = lvf.src(r'BDMV/HIGURASHI_BD/00011.m2ts')
src = lvf.decomb(src, TFF=True)[:-24]
src = fvf.Depth(src, 32)
crop = core.std.CropAbs(src, x=4, y=0, width=712, height=480)


planes = split(crop)
planes[0] = nnedi3_rpow2(planes[0]).resize.Bicubic(get_w(576, 20/11), 576)
planes[1], planes[2] = [core.resize.Bicubic(p, planes[0].width/2, planes[0].height/2) for p in planes[1:]]
upscaled = fvf.Depth(join(planes), 16)

# usually I avoid warping like the plague, but it looks "ok" here
warp = core.warp.AWarpSharp2(upscaled, thresh=36, blur=1, type=1, depth=12)
sharpen = haf.LSFmod(warp, strength=60, soft=10, edgemode=1, Smethod=2, Lmode=2).rgvs.Repair(upscaled, 13)
aa = lvf.upscaled_sraa(sharpen)
darken = haf.FastLineDarkenMOD(aa, strength=18, protection=11, threshold=0)


l_mask = kgf.retinex_edgemask(darken, 10).std.Binarize()
sqmask = kgf.squaremask(darken, upscaled.width, 256, 0, 170).std.Invert()
l_mask = core.std.Expr([l_mask, sqmask], "x y -")

denoise_a = mvf.BM3D(darken, sigma=[0.4,0.2], depth=16)
denoise_b = mvf.BM3D(darken, sigma=[7,0.2], depth=16)

deband_a = core.f3kdb.Deband(denoise_a, range=15, preset="medium/nograin", output_depth=16)
deband_b = core.f3kdb.Deband(denoise_b, range=5, preset="medium/nograin", output_depth=16)
deband_b = core.f3kdb.Deband(deband_b, range=21, preset="medium", output_depth=16)

# Fixing banding behind the big splotches of grain during the Rena OP scene
diff = core.std.MakeDiff(darken, denoise_b)
deband_c = core.std.MergeDiff(deband_b, diff)

deband = fvf.rfs(deband_a, deband_b, mappings=f"[{opstart+329} {opstart+499}] [{opstart+1170} {opstart+1178}]")
deband = fvf.rfs(deband, deband_c, mappings=f"[{opstart+1032} {opstart+1169}]")
deband = core.std.MaskedMerge(deband, darken, l_mask)

grain = kgf.adaptive_grain(deband, 0.1, luma_scaling=8)


out = grain
final = fvf.Depth(out, 10)
final.set_output()
