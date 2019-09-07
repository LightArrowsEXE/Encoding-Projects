import vapoursynth as vs
import fvsfunc as fvf
import kagefunc as kgf
import lvsfunc as lvf
import mvsfunc as mvf
from vsTAAmbk import TAAmbk
from nnedi3_rpow2 import nnedi3_rpow2
from vsutil import get_w
core = vs.core

opstart, edstart = 0, None
b, c = 1/5, 2/5

src = lvf.src(r"BDMV/[BDMV][190731][Kimetsu no Yaiba][Vol.1]/BDMV/STREAM/00007.m2ts")
src = src[:2160]
src = fvf.Depth(src, 16)


y, u, v = kgf.split(src)
descaled = core.descale.Debicubic(fvf.Depth(y, 32), get_w(855), 855, b, c)

w2x = core.resize.Point(mvf.ToYUV(core.w2xc.Waifu2x(mvf.ToRGB(descaled), noise=1, scale=1, gpu=0)), format=descaled.format)
w2x = fvf.rfs(descaled, w2x, mappings=f"{opstart+1593} {opstart+1594}")

denoise = mvf.BM3D(w2x, sigma=1)
denoise = fvf.Depth(denoise, 16)

aa = TAAmbk(denoise, aatype='Eedi3')
aa = fvf.rfs(denoise, aa, mappings=f"[{opstart+284} {opstart+406}] [{opstart+1017} {opstart+1079}] [{opstart+1312} {opstart+1368}] {opstart+1593} {opstart+1594} [{opstart+1895} {opstart+2003}]")

upscaled = nnedi3_rpow2(aa).resize.Bicubic(src.width, src.height)
upscaled = kgf.join([upscaled, u, v])

deband_a = core.f3kdb.Deband(upscaled, range=16, y=32, cb=40, cr=40, grainy=24, grainc=0, output_depth=16, sample_mode=1)
deband_b = core.f3kdb.Deband(upscaled, range=18, y=40, cb=48, cr=48, grainy=36, grainc=0, output_depth=16, sample_mode=1)
deband = fvf.rfs(deband_a, deband_b, mappings=f"[{opstart+742} {opstart+784}] [{opstart+1128} {opstart+1287}] [{opstart+1592} {opstart+1616}] [{opstart+2004} {opstart+2046}]")

grain_a = kgf.adaptive_grain(deband, 0.3, luma_scaling=4)
grain_b = kgf.adaptive_grain(deband, 1)
grain_c = core.grain.Add(deband, 10, constant=False)
grain = fvf.rfs(grain_a, grain_b, mappings=f"[{opstart+1128} {opstart+1296}]")
grain = fvf.rfs(grain, grain_c, mappings=f"[{opstart+28} {opstart+288}] [{opstart+401} {opstart+406}] [{opstart+1313} {opstart+1368}]")


out = grain
final = fvf.Depth(out, 10)
final.set_output()
