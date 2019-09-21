import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import havsfunc as haf
import mvsfunc as mvf
from vsTAAmbk import TAAmbk
core = vs.core


src = lvf.src(r'_-XGfDXi7t-rI.mkv')
src = core.vivtc.VDecimate(src)
src = fvf.Depth(src, 16)


scaled = core.resize.Bicubic(src, 1280, 720, format=vs.YUV444P16)

d_mask = kgf.adaptive_grain(scaled, show_mask=True, luma_scaling=18)
denoise_a = mvf.BM3D(scaled, sigma=[0.8,0.4])
denoise_b = mvf.BM3D(scaled, sigma=[1.8,0.9])
denoise = core.std.MaskedMerge(denoise_a, denoise_b, d_mask)


sharpen = haf.LSFmod(denoise, strength=120, soft=20, edgemode=1, Smethod=2, Lmode=2)
aa = TAAmbk(sharpen, aatype='Nnedi3')
dering = haf.HQDeringmod(aa, nrmode=2, darkthr=0, sharp=0, mthr=40)


deband_a = core.f3kdb.Deband(dering, range=14, y=32, cb=24, cr=24, grainy=36, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(dering, range=16, y=32, cb=24, cr=24, grainy=36, grainc=0, output_depth=16)
deband_c = core.f3kdb.Deband(dering, range=18, y=40, cb=32, cr=32, grainy=48, grainc=0, output_depth=16)
deband = core.std.MaskedMerge(deband_a, deband_b, d_mask)
deband = fvf.rfs(deband, deband_c, mappings="[1098 1115] [1125 1204]")


grain_a = kgf.adaptive_grain(deband, 0.5, luma_scaling=8)
grain_b = kgf.adaptive_grain(deband, 1, static=False, luma_scaling=4)
grain = fvf.rfs(grain_a, grain_b, mappings="[0 24] [199 404] [1065 1074] [1078 1086] [1125 1136] [1205 1214] [1951 2028]")


out = grain
final = fvf.Depth(out, 10)
final.set_output()
