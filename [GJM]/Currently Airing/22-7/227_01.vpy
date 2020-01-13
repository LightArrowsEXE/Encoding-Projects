import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import mvsfunc as mvf
import havsfunc as haf
from vsutil import *
from cooldegrain import *
from nnedi3_rpow2 import *
core = vs.core


src = lvf.src(r"01/227 - 01v2 (Funimation 1080p).mkv")
src = src[289:]
ef = core.edgefixer.ContinuityFixer(src, 1, 1, 1, 1)
shift = haf.FixChromaBleedingMod(ef, cx=-0.25, cy=-0.25, thr=100, strength=1, blur=True)
shift = fvf.Depth(shift, 32)


h = 900
b, c =  1/5, 2/5
planes = split(shift)
descaled = core.descale.Debicubic(planes[0], get_w(h), h, b, c)
upscaled = core.resize.Bicubic(descaled, planes[0].width, planes[0].height, filter_param_a=b, filter_param_b=c)
credit_mask = core.std.Expr([planes[0], upscaled], 'x y - abs').std.Binarize(0.05)
credit_mask = kgf.iterate(credit_mask, core.std.Maximum, 6)
credit_mask = kgf.iterate(credit_mask, core.std.Inflate, 2)

descaled = nnedi3_rpow2(descaled).resize.Spline36(planes[0].width, planes[0].height)
planes[0] = core.std.MaskedMerge(descaled, planes[0], credit_mask)
scaled = join(planes)


debl = fvf.Depth(core.deblock.Deblock(scaled, quant=18), 16)
dering = haf.EdgeCleaner(debl, strength=2, rmode=13, smode=1)
deband = core.f3kdb.Deband(dering, range=16, y=32, cb=24, cr=24, grainy=12, grainc=0, output_depth=16)
grain = kgf.adaptive_grain(deband, 0.1, luma_scaling=6)


out = grain
final = fvf.Depth(out, 10)
final.set_output()
