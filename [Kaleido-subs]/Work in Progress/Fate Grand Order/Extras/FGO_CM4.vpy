import vapoursynth as vs
import lvsfunc as lvf
import fvsfunc as fvf
import kagefunc as kgf
import havsfunc as haf
import vsTAAmbk as taa
from nnedi3_rpow2 import nnedi3_rpow2
core = vs.core
core.max_cache_size = 8096

src = lvf.src(r"../Fate Grand Order -First Order-/BDROM/BDMV/STREAM/00005.m2ts")
src = src[24:384]
src = fvf.Depth(src, 16)
Y, U, V = kgf.split(src)

scaled = kgf.inverse_scale(src, height=873, kernel='bicubic', a1=0, a2=1)
scaled = nnedi3_rpow2(scaled).resize.Spline36(1920, 1080, format=vs.YUV420P16)
scaled_m = kgf.inverse_scale(src, height=873, kernel='bicubic', mask_detail=True, show_mask=True).resize.Spline36(1920, 1080, format=vs.GRAY16)
scaled = core.std.MaskedMerge(scaled, src, scaled_m)
scaled = kgf.join([scaled, U, V])

denoise = lvf.qden(scaled, h=1.4, sigma=6)
deband = core.f3kdb.Deband(denoise, range=17, y=40, cb=32, cr=32, grainy=0, grainc=0, output_depth=16)
contraSharpen = haf.ContraSharpening(deband, src, radius=None, rep=13)

sharpen = haf.LSFmod(scaled, strength=150, soft=10, edgemode=1, Smethod=2, Lmode=2)
aa_a = taa.TAAmbk(sharpen, aatype='Eedi3', opencl=True)
aa_b = taa.TAAmbk(sharpen, aatype='Eedi3SangNom', opencl=True)
aa = fvf.rfs(aa_a, aa_b, mappings='[60 69] [222 267]')

mask = kgf.retinex_edgemask(aa, 1)
maskedmerge = core.std.MaskedMerge(contraSharpen, aa, mask)

out = maskedmerge
final = fvf.Depth(out, 10)
final.set_output()