import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import vsTAAmbk as taa
from nnedi3_rpow2 import nnedi3_rpow2
core = vs.core
core.max_cache_size = 8192

src = lvf.src(r"Zesty Fries/00006.m2ts")
src = src[29921:32846]
src = fvf.Depth(src, 16)
Y, U, V = kgf.split(src)

scaled = kgf.inverse_scale(src, kernel='bicubic', height=855, a1=0, a2=1, mask_detail=True, masking_areas=[[840,903],[2839,2924]])
scaled = nnedi3_rpow2(scaled).resize.Spline36(1920, 1080)
scaled = fvf.Depth(scaled, 16)
scaled = kgf.join([scaled, U, V])

aa_a = taa.TAAmbk(scaled, aatype='Eedi3', opencl=True)
aa_b = taa.TAAmbk(scaled, aatype='Eedi3SangNom', opencl=True)
aa = fvf.rfs(aa_a, aa_b, mappings="[434 498]")

denoise = lvf.quick_denoise(scaled, h=1.2, sigma=5)
deband = core.f3kdb.Deband(denoise, range=18, y=40, cb=32, cr=32, grainy=0, grainc=0, output_depth=16)

mask = kgf.retinex_edgemask(src)
merge = core.std.MaskedMerge(deband, aa, mask)

grain = kgf.adaptive_grain(merge, 0.7, luma_scaling=20)

out = grain
final = fvf.Depth(out, 10)
comp = lvf.comp(src, out, [478, 652, 831, 903, 927, 953, 1026, 1206, 1298, 1409, 1751, 1834, 1848, 2022, 2146, 2470, 2532, 2649])
final.set_output()
