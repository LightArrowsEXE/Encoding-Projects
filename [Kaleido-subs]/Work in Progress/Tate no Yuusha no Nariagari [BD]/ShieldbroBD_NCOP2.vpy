import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import vsTAAmbk as taa
import havsfunc as haf
from nnedi3_rpow2 import nnedi3_rpow2
core = vs.core

opstart = 0

src = lvf.src(r"BDMV/[BDMV][190524][Tate no Yuusha no Nariagari][Vol.2]/TATE_2_2/BDMV/STREAM/00012.m2ts")
src = src[24:2183]
src = fvf.Depth(src, 16)


denoise = lvf.quick_denoise(src, h=1, sigma=4)
aa = taa.TAAmbk(denoise, aatype='Nnedi3SangNom', sharp=120, repair=2)

deband_a = core.f3kdb.Deband(aa, range=17, y=40, cb=32, cr=32, grainy=0, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(aa, range=21, y=72, cb=64, cr=64, grainy=12, grainc=0, output_depth=16)
deband = fvf.rfs(deband_a, deband_b, mappings=f"[{opstart+487} {opstart+558}] [{opstart+958} {opstart+997}]")

grain_a = kgf.adaptive_grain(deband_a, 0.3)
grain_b = kgf.adaptive_grain(deband_b, 3, static=False, luma_scaling=8)
grain = fvf.rfs(grain_a, grain_b, mappings="[{opstart+925} {opstart+1196}]")


out = grain
final = fvf.Depth(out, 10)
final.set_output()
