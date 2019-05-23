import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import mvsfunc as mvf
import vsTAAmbk as taa
import havsfunc as haf
core = vs.core
core.max_cache_size = 8192

src = lvf.src(r"movie_max.mp4").std.AssumeFPS(fpsnum=24000, fpsden=1001)
src = src[:1792]+src[1793:2280]
scaled_c = core.resize.Spline36(src, 1280, 720, format=vs.YUV444P16)
src = fvf.AutoDeblock(src)

scaled = core.resize.Spline36(src, 1280, 720, format=vs.YUV444P16)
scaled = core.std.CropRel(scaled, left=0, right=0, top=88, bottom=88)
scaled = core.edgefixer.ContinuityFixer(scaled, left=[2,2,2],top=[2,2,2],bottom=[2,2,2], right=[2,2,2], radius=[3,3,3])
scaled = core.std.AddBorders(scaled, left=0, right=0, top=88, bottom=88)
scaled = fvf.Depth(scaled, 16)

sharpen = haf.LSFmod(scaled, strength=64, soft=10, edgemode=1, Smethod=2, Lmode=2)
aa = taa.TAAmbk(sharpen, aatype='Eedi3')
deband_a = core.f3kdb.Deband(aa, range=10, y=24, cb=16, cr=16, grainy=0, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(aa, range=14, y=32, cb=24, cr=24, grainy=12, grainc=0, output_depth=16)
deband = fvf.rfs(deband_a, deband_b, mappings="[1223 1250]")

grain_a = kgf.adaptive_grain(deband, 0.3)
grain_b = kgf.adaptive_grain(deband, 2, static=False)
grain = fvf.rfs(grain_a, grain_b, mappings="[155 373]")

out = grain
final = fvf.Depth(out, 10)
comp = lvf.comp(scaled_c, out, [153, 351, 438, 559, 708, 828, 881, 973, 1093, 1337, 1461, 1475, 1483, 1513, 1566, 1657, 1679, 1695, 1710, 1750, 1815, 1819, 1844, 1849, 1877, 1977, 2009, 2010, 2025, 2026, 2041, 2042, 2057, 2058])
final.set_output()

