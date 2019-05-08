import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import vsTAAmbk as taa
import havsfunc as haf
from nnedi3_rpow2 import nnedi3_rpow2

opstart = 0

src = lvf.src(r"BDMV/[BDMV][190424][Tate no Yuusha no Nariagari][Vol.1]/TATE_1_2/BDMV/STREAM/00013.m2ts")
src = src[24:2182]
src = fvf.Depth(src, 16)

denoise = lvf.quick_denoise(src, h=1, sigma=4)
denoise = fvf.rfs(denoise, src, mappings="[0 1215]")

aa = taa.TAAmbk(denoise, aatype='Nnedi3SangNom', sharp=120, repair=2)

deband_a = core.f3kdb.Deband(aa, range=17, y=40, cb=32, cr=32, grainy=0, grainc=0, output_depth=16)
grain_a = kgf.adaptive_grain(deband_a, 0.3)
deband_b = core.f3kdb.Deband(aa, range=21, y=72, cb=64, cr=64, grainy=12, grainc=0, output_depth=16)
grain_b = kgf.adaptive_grain(deband_b, 3, static=False, luma_scaling=8)
grain = fvf.rfs(grain_a, grain_b, mappings=f"[{opstart} {opstart+79}]")

out = grain
final = fvf.Depth(out, 10)
final.set_output()