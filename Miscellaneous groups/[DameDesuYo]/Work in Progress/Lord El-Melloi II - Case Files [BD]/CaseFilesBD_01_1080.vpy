import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import mvsfunc as mvf
from vsTAAmbk import TAAmbk
from nnedi3_rpow2 import nnedi3_rpow2
core = vs.core

src = lvf.src(r'BDMV/[BDMV] Lord El-Melloi II Sei no Jikenbo/Vol 1/BDROM/BDMV/STREAM/00001.m2ts')
src = src[24:-24]
src = fvf.Depth(src, 32)


b, c = 0, 1/2
y, u, v = kgf.split(src)
descaled = core.descale.Debicubic(y, 1280, 720, b, c)
upscaled = core.resize.Bicubic(descaled, y.width, y.height, filter_param_a=b, filter_param_b=c)
credit_mask = core.std.Expr([y, upscaled], 'x y - abs').std.Binarize(0.05)
credit_mask = kgf.iterate(credit_mask, core.std.Maximum, 6)
credit_mask = kgf.iterate(credit_mask, core.std.Inflate, 2)

denoise = mvf.BM3D(descaled, sigma=[2,1])

mask = kgf.retinex_edgemask(fvf.Depth(descaled, 16))
merge = core.std.MaskedMerge(denoise, descaled, fvf.Depth(mask, 32))

upscaled = nnedi3_rpow2(merge).resize.Bicubic(src.width, src.height)
upscaled = kgf.join([upscaled, u, v])


deband = core.f3kdb.Deband(fvf.Depth(upscaled, 16), range=17, y=32, cb=24, cr=24, grainy=64, grainc=0, output_depth=16)
grain = kgf.adaptive_grain(deband, 0.15, luma_scaling=6)


out = grain
final = fvf.Depth(out, 10)
final.set_output()
