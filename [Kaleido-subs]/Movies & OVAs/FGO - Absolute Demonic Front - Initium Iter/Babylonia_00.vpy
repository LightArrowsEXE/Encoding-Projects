import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import mvsfunc as mvf
from vsTAAmbk import TAAmbk
from vsutil import *
from nnedi3_rpow2 import nnedi3_rpow2
core = vs.core


src = lvf.src('[Erai-raws] Fate Grand Order - Zettai Majuu Sensen Babylonia - Initium Iter - 00 [1080p][Multiple Subtitle].mkv')
src = fvf.Depth(src, 32)


y, u, v = kgf.split(src)
b, c = 1/3, 1/3
descaled = core.descale.Debicubic(y, get_w(873), 873, b=b, c=c)
upscaled = core.resize.Bicubic(descaled, src.width, src.height, filter_param_a=b, filter_param_b=c)
credit_mask = core.std.Expr([fvf.Depth(y, 32), upscaled], 'x y - abs').std.Binarize(0.05)
credit_mask = kgf.iterate(credit_mask, core.std.Maximum, 6)
credit_mask = kgf.iterate(credit_mask, core.std.Inflate, 2)

aa = fvf.Depth(TAAmbk(fvf.Depth(descaled, 16), aatype='Eedi3', repair=2), 32)

scaled = nnedi3_rpow2(aa).resize.Bicubic(src.width, src.height)
scaled = core.std.MaskedMerge(scaled, y, credit_mask)
scaled = kgf.join([scaled, u, v])


denoise = fvf.Depth(mvf.BM3D(scaled, sigma=[1.5,0.5]), 16)

d_mask = kgf.adaptive_grain(fvf.Depth(src, 16), show_mask=True, luma_scaling=6)
deband_a = core.f3kdb.Deband(denoise, range=16, y=32, cb=24, cr=24, grainy=24, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(denoise, range=18, y=40, cb=32, cr=32, grainy=48, grainc=0, output_depth=16)
deband = core.std.MaskedMerge(deband_a, deband_b, d_mask)


sqmask = kgf.squaremask(fvf.Depth(src, 16), 1920, 752, 0, 165)
grain_a = kgf.adaptive_grain(deband, 0.3, luma_scaling=6)
grain_b = core.grain.Add(deband, 10, constant=True)
grain_b = core.std.MaskedMerge(deband, grain_b, sqmask)
grain = fvf.rfs(grain_a, grain_b, mappings="[21536 22177]")


out = deband
final = fvf.Depth(out, 10)
final.set_output()
