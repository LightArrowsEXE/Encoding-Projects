import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
from cooldegrain import *
from nnedi3_rpow2 import *
from vsutil import *
core = vs.core


src = lvf.src(r'BDMV/GRANBLUE_FANTASY_SEASON2_1/BDMV/STREAM/00002.m2ts')
src = fvf.Depth(src, 32)
src = src[:-27]

h = 844
b, c = 0, 1/2
planes = split(src)
descaled = core.descale.Debicubic(planes[0], get_w(h), h, b=b, c=c)
upscaled = core.resize.Bicubic(descaled, planes[0].width, planes[0].height, filter_param_a=b, filter_param_b=c)
credit_mask = core.std.Expr([planes[0], upscaled], 'x y - abs').std.Binarize(0.05)
credit_mask = kgf.iterate(credit_mask, core.std.Maximum, 6)
credit_mask = kgf.iterate(credit_mask, core.std.Inflate, 2)

planes[0] = nnedi3_rpow2(descaled).resize.Bicubic(planes[0].width, planes[0].height, filter_param_a=0, filter_param_b=1/2)
upscaled = join(planes)

scaled = core.std.MaskedMerge(upscaled, src, credit_mask)


d_mask = kgf.adaptive_grain(fvf.Depth(scaled, 16), show_mask=True, luma_scaling=10)
denoise_a = CoolDegrain(scaled, tr=1, thsad=72, thsadc=48, bits=16, blksize=8, overlap=4)
denoise_b = CoolDegrain(scaled, tr=1, thsad=24, thsadc=48, bits=16, blksize=8, overlap=4)
denoise = core.std.MaskedMerge(denoise_a, denoise_b, d_mask)

deband = core.f3kdb.Deband(denoise, range=18, y=40, cb=32, cr=32, grainy=36, grainc=0, output_depth=16)
grain = kgf.adaptive_grain(deband, 0.2, luma_scaling=7)


out = grain
final = fvf.Depth(out, 10)
final.set_output()
