import vapoursynth as vs
import lvsfunc as lvf
import fvsfunc as fvf
import kagefunc as kgf
import havsfunc as haf
import vsTAAmbk as taa
from nnedi3_rpow2 import nnedi3_rpow2
core = vs.core
core.max_cache_size = 8096

src = lvf.src(r"../Fate Grand Order -First Order-/BDROM/BDMV/STREAM/00013.m2ts")
src = src[24:384]
src = fvf.Depth(src, 16)
Y, U, V = kgf.split(src)

scaled = kgf.inverse_scale(src, height=720, kernel='bicubic')
scaled = nnedi3_rpow2(scaled).resize.Spline36(1920, 1080, format=vs.YUV420P16)
scaled_m = kgf.inverse_scale(src, height=720, kernel='bicubic', mask_detail=True, show_mask=True).resize.Spline36(1920, 1080, format=vs.GRAY16)
scaled = core.std.MaskedMerge(scaled, src, scaled_m)
scaled = kgf.join([scaled, U, V])

denoise_a = lvf.qden(scaled, h=1.2)
deband_a = core.f3kdb.Deband(denoise_a, range=17, y=32, cb=24, cr=24, grainy=0, grainc=0, output_depth=16)
sharpen_a = haf.ContraSharpening(deband_a, src, radius=None, rep=13)

denoise_b = lvf.qden(scaled, h=4, sigma=10)
deband_b = core.f3kdb.Deband(denoise_b, range=8, y=80, cb=72, cr=72, grainy=0, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(deband_b, range=21, y=64, cb=56, cr=56, grainy=24, grainc=0, output_depth=16)
dbn_mask = kgf.adaptive_grain(src, show_mask=True)
deband_b = core.std.MaskedMerge(deband_a, deband_b, dbn_mask)
grain_b = kgf.adaptive_grain(deband_b, 1)
sharpen_b = haf.ContraSharpening(grain_b, src, radius=None, rep=13)

sharpen = fvf.rfs(sharpen_a, sharpen_b, "[216 255]")

aa = taa.TAAmbk(scaled, aatype='Eedi3', opencl=True)

mask = kgf.retinex_edgemask(aa, 1)
maskedmerge = core.std.MaskedMerge(sharpen, aa, mask)

out = maskedmerge
final = fvf.Depth(out, 10)
final.set_output()