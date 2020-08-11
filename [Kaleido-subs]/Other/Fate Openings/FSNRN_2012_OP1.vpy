import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import vsTAAmbk as taa
import havsfunc as haf
from nnedi3_rpow2 import nnedi3_rpow2
core = vs.core
core.max_cache_size = 8192

src = lvf.src(r"src/[BDMV][120919][Fate Zero][Blu-ray Disc BOX 2]/Fate／Zero Blu-ray Disc Box Ⅱ Disc5 +特典CD/BDROM/BDMV/STREAM/00008.m2ts")
src = src[840:3000]
src = fvf.Depth(src, 16)
Y, U, V = kgf.split(src)

scaled = kgf.inverse_scale(src, height=855, kernel='bicubic', a1=0, a2=1)
scaled = fvf.Depth(scaled, 16)
Y2, U2, V2 = kgf.split(scaled)

denoise_a = lvf.quick_denoise(Y2, h=1.4, sigma=4)
denoise_b = lvf.quick_denoise(Y2, h=3, sigma=10)
denoise = fvf.rfs(denoise_a, denoise_b, mappings="[370 468]")

sharpen = haf.LSFmod(denoise, strength=100, soft=10, edgemode=1, Smethod=2, Lmode=2)
aa = taa.TAAmbk(sharpen, aatype='Eedi3')
scaled = nnedi3_rpow2(aa).resize.Spline36(1920, 1080)
scaled = kgf.join([scaled, U, V])

deband_a = core.f3kdb.Deband(scaled, range=16, y=32, cb=24, cr=24, grainy=12, grainc=0, output_depth=16)
grain_a = kgf.adaptive_grain(deband_a, 1, luma_scaling=16)
deband_b = core.f3kdb.Deband(scaled, range=21, y=40, cb=32, cr=32, grainy=24, grainc=0, output_depth=16)
grain_b = kgf.adaptive_grain(deband_b, 5, luma_scaling=16)
grain = fvf.rfs(grain_a, grain_b, mappings="[370 468]")


out = grain
final = fvf.Depth(out, 10)
final.set_output()
