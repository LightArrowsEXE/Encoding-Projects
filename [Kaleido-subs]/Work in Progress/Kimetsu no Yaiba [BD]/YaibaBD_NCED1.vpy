import vapoursynth as vs
import fvsfunc as fvf
import kagefunc as kgf
import lvsfunc as lvf
import mvsfunc as mvf
from vsTAAmbk import TAAmbk
from nnedi3_rpow2 import nnedi3_rpow2
from vsutil import get_w
core = vs.core

opstart, edstart = None, 0
b, c = 1/5, 2/5

src = lvf.src(r"BDMV/[BDMV][190731][Kimetsu no Yaiba][Vol.1]/BDMV/STREAM/00008.m2ts")
src = src[:2160]
src = fvf.Depth(src, 16)


y, u, v = kgf.split(src)
descaled = core.descale.Debicubic(fvf.Depth(y, 32), get_w(855), 855, b, c)

denoise = mvf.BM3D(descaled, sigma=1)
denoise = fvf.Depth(denoise, 16)

aa = TAAmbk(denoise, aatype='Eedi3')
aa = fvf.rfs(denoise, aa, mappings=f"[{edstart+890} {edstart+1032}]")

upscaled = nnedi3_rpow2(aa).resize.Bicubic(src.width, src.height)
upscaled = kgf.join([upscaled, u, v])


deband_a = core.f3kdb.Deband(upscaled, range=17, y=32, cb=32, cr=32, grainy=24, grainc=0, output_depth=16, sample_mode=1)
deband_b = core.f3kdb.Deband(upscaled, range=19, y=48, cb=48, cr=48, grainy=36, grainc=0, output_depth=16, sample_mode=1)
deband = fvf.rfs(deband_a, deband_b, mappings=f"[{edstart+1494} {edstart+1600}]")

grain = kgf.adaptive_grain(deband, 0.3, luma_scaling=4)


out = grain
final = fvf.Depth(out, 10)
final.set_output()
