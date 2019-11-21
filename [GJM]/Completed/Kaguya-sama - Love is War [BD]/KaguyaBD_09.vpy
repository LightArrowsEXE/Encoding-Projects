import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import havsfunc as haf
import mvsfunc as mvf
from vsutil import *
from cooldegrain import *
core = vs.core


src = lvf.src(r"BDMV/かぐや様は告らせたい Vol.5/BD/BDMV/STREAM/00001.m2ts")
src = src[:-25]
ef = core.edgefixer.ContinuityFixer(src, 1, 1, 1, 1)
shift = haf.FixChromaBleedingMod(ef, cx=0.5, cy=0, thr=100, strength=1, blur=True)
shift = fvf.Depth(shift, 32)


planes = split(shift)
planes[0] = fvf.DescaleAA(planes[0], get_w(874), 874, kernel='bicubic', b=0, c=1/2)
scaled = join(planes)

ref = mvf.BM3D(src, sigma=[4,0], depth=16, profile1="lc")
ref = core.f3kdb.Deband(ref, output_depth=16, range=18, preset="high/luma/nograin")
d_mask = kgf.adaptive_grain(ref, show_mask=True, luma_scaling=24)
l_mask = kgf.retinex_edgemask(ref)
den_mask = fvf.Depth(core.std.Expr([d_mask, l_mask], "x y +"), 16)

denoise_a = mvf.BM3D(scaled, sigma=[.8, 1], depth=16)
denoise_b = CoolDegrain(scaled, tr=1, thsad=24, thsadc=48, bits=16, blksize=8, overlap=4)
denoise = core.std.MaskedMerge(denoise_a, denoise_b, den_mask)

deband_a = core.f3kdb.Deband(denoise, range=16, output_depth=16, preset="medium/nograin")
deband_b = core.f3kdb.Deband(denoise, range=14, output_depth=16, preset="medium")
denoise = core.std.MaskedMerge(deband_a, deband_b, fvf.Depth(d_mask, 16))

grain = kgf.adaptive_grain(denoise, 0.2, luma_scaling=6)


out = grain
final = fvf.Depth(out, 10)
final.set_output()
