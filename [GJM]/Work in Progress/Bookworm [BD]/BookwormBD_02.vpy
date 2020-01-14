import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import mvsfunc as mvf
from vsutil import *
from vsTAAmbk import *
core = vs.core
core.num_threads = 4

opstart = 3548-2157 # final frame of the OP - 2157

src = lvf.src(r"BDMV/[BDMV] HONZUKI/HONZUKI_1/BDMV/STREAM/00002.m2ts")
src = src[24:-24]
src = fvf.Depth(src, 32)


h1, h2 = 812, 810
b, c = 0.3782, 0.3109 # robidoux soft
planes = split(src)
# Descaling & create credit mask
downscaled = core.resize.Bicubic(src, get_w(h2), h2, format=vs.YUV444PS)
descaled = core.descale.Debicubic(planes[0], get_w(h1), h1, b, c)
upscaled = core.resize.Bicubic(descaled, planes[0].width, planes[0].height, filter_param_a=b, filter_param_b=c)

credit_mask = core.std.Expr([planes[0], upscaled], 'x y - abs').std.Binarize(0.05)
credit_mask = kgf.iterate(credit_mask, core.std.Maximum, 6)
credit_mask = kgf.iterate(credit_mask, core.std.Inflate, 4)
credit_mask = core.resize.Bicubic(credit_mask, downscaled.width, downscaled.height)

planes[0] = core.resize.Bicubic(descaled, downscaled.width, downscaled.height)
planes[1], planes[2] = [core.resize.Bicubic(p, planes[0].width, planes[0].height, src_left=.25) for p in planes[1:]]
scaled = join(planes)
scaled = core.std.MaskedMerge(scaled, downscaled, credit_mask)
scaled = fvf.rfs(scaled, downscaled, mappings=f"[{src.num_frames-120} {src.num_frames-1}]")


d_mask = kgf.adaptive_grain(fvf.Depth(downscaled, 16), show_mask=True, luma_scaling=8)
denoise_a = mvf.BM3D(scaled, sigma=[2,1.5], depth=16, profile1='lc')
denoise_b = mvf.BM3D(scaled, sigma=[1,0.5], depth=16, profile1='lc')
denoise = core.std.MaskedMerge(denoise_a, denoise_b, d_mask)
denoise = fvf.rfs(denoise, denoise_a, mappings=f"[{opstart+249} {opstart+568}]")


aa = TAAmbk(denoise, aatype='Eedi3', repair=2)
l_mask = kgf.retinex_edgemask(aa, 1.5)


deband_a = core.f3kdb.Deband(aa, range=18, y=40, cb=32, cr=32, grainy=0, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(aa, range=16, y=24, cb=16, cr=16, grainy=0, grainc=0, output_depth=16)
deband_c = core.f3kdb.Deband(aa, range=23, y=40, cb=32, cr=32, grainy=24, grainc=0, output_depth=16)
deband = core.std.MaskedMerge(deband_a, deband_b, d_mask)
deband = fvf.rfs(deband, deband_c, mappings=f"[{opstart+249} {opstart+568}]")
deband = core.std.MaskedMerge(deband, aa, l_mask)


grain = kgf.adaptive_grain(deband, 0.15, luma_scaling=6)


out = grain
final = fvf.Depth(out, 10)
final.set_output()
