import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import vsTAAmbk as taa
import havsfunc as haf
from nnedi3_rpow2 import nnedi3_rpow2
core = vs.core
core.max_cache_size = 8192

src = lvf.src(r"BDMV/[BDMV][190424][Tate no Yuusha no Nariagari][Vol.1]/TATE_1_2/BDMV/STREAM/00014.m2ts")
src = src[24:2182]
src = fvf.Depth(src, 16)


aa = taa.TAAmbk(src, aatype='Nnedi3SangNom', sharp=120, repair=2)
deband = core.f3kdb.Deband(aa, range=17, y=40, cb=32, cr=32, grainy=0, grainc=0, output_depth=16)
grain = kgf.adaptive_grain(deband, 0.3)


out = grain
final = fvf.Depth(out, 10)
final.set_output()
