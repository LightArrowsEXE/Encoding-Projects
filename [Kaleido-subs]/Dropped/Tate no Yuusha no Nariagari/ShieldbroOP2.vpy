import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import vsTAAmbk as taa
import havsfunc as haf
import adjust
from nnedi3_rpow2 import nnedi3_rpow2
core = vs.core

opstart = 0

src = lvf.src(r"15/The Rising of the Shield Hero E15 [1080p][AAC][JapDub][GerEngSub][Web-DL].mkv")
src = src[1990:4149]
src = fvf.Depth(src, 16)

dim1 = adjust.Tweak(src, sat=1.1, cont=1.1, bright=0)
dim2 = adjust.Tweak(src, sat=1.25, cont=1.25, bright=0)
dim3 = adjust.Tweak(src, sat=1.4, cont=1.4, bright=0)
dimming = fvf.rfs(src, dim1, mappings="1832 1849 ")
dimming = fvf.rfs(dimming, dim2, mappings="1833 1848")
dimming = fvf.rfs(dimming, dim3, mappings="[1834 1847]")

mask = lvf.src(r"15/ShieldbroEp15_mask.png").resize.Spline36(format=vs.YUV420P16, matrix_s='709').std.Minimum().std.Minimum()
dim4 = adjust.Tweak(src, sat=1.3, cont=1.1, bright=0)
dim4 = core.std.MaskedMerge(dim4, src, mask)
dimming = fvf.rfs(dimming, dim4, mappings="[1863 1891]")

sharp = haf.LSFmod(dimming, strength=80, soft=10, edgemode=1, Smethod=2, Lmode=2)
aa = taa.TAAmbk(sharp, aatype='Nnedi3SangNom')

deband_a = core.f3kdb.Deband(aa, range=17, y=40, cb=32, cr=32, grainy=0, grainc=0, output_depth=16)
grain_a = kgf.adaptive_grain(deband_a, 0.3)
deband_b = core.f3kdb.Deband(aa, range=21, y=72, cb=64, cr=64, grainy=12, grainc=0, output_depth=16)
grain_b = core.grain.Add(deband_b, var=3, uvar=0, constant=False)
deband_c = core.f3kdb.Deband(aa, range=21, y=72, cb=64, cr=64, grainy=12, grainc=0, output_depth=16)
grain_c = kgf.adaptive_grain(deband_a, 3, static=False, luma_scaling=8)
deband_d = core.f3kdb.Deband(aa, range=18, y=56, cb=48, cr=48, grainy=12, grainc=0, output_depth=16)
grain_d = kgf.adaptive_grain(deband_d, 1, static=False, luma_scaling=8)
grain = fvf.rfs(grain_a, grain_b, mappings=f"[{opstart} {opstart+48}] [{opstart+487} {opstart+558}]")
grain = fvf.rfs(grain, grain_c, mappings=f" [{opstart+633} {opstart+1206}]")
grain = fvf.rfs(grain, grain_d, mappings=f"[{opstart+121} {opstart+193}]")

out = grain
final = fvf.Depth(out, 10)
comp = lvf.comp(src, out, [135, 498, 538, 740, 877, 973, 1102, 1196, 1223, 1415, 1429, 1583, 1620, 1835, 1861, 1918, 1986, 2057, 2158])
comp.set_output()