import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import mvsfunc as mvf
import havsfunc as haf
from vsTAAmbk import TAAmbk
from nnedi3_rpow2 import nnedi3_rpow2
from vsutil import *
core = vs.core

src = lvf.src(r'G:/src/[BDMV] Lord El-Melloi II Sei no Jikenbo/Vol 1/BDROM/BDMV/STREAM/00000.m2ts')
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
merge = fvf.Depth(core.std.MaskedMerge(denoise, descaled, fvf.Depth(mask, 32)), 16)

lmask = fvf.Depth(core.std.Binarize(get_y(merge), 0.25).std.Maximum().std.Inflate(), 16)
aa = TAAmbk(merge, aatype='Eedi3', mclip=lmask, cycle=1)
motion = haf.QTGMC(aa, InputType=1, TR2=3)
aa = core.std.MaskedMerge(aa, motion, lmask)
aa = fvf.Depth(fvf.rfs(merge, aa, mappings="[22787 22902]"), 32)

upscaled = nnedi3_rpow2(aa).resize.Bicubic(src.width, src.height)
upscaled = kgf.join([upscaled, u, v])


deband = core.f3kdb.Deband(fvf.Depth(upscaled, 16), range=16, y=32, cb=24, cr=24, grainy=64, grainc=0, output_depth=16)
grain = kgf.adaptive_grain(deband, 0.15, luma_scaling=6)


out = grain
final = fvf.Depth(out, 10)
final.set_output()
