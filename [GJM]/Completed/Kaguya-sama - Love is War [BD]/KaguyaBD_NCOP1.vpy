import fvsfunc as fvf
import havsfunc as haf
import kagefunc as kgf
import lvsfunc as lvf
import mvsfunc as mvf
from awsmfunc import bbmod
from cooldegrain import CoolDegrain
from vsutil import depth

import vapoursynth as vs

core = vs.core


src = lvf.src(r"BDMV/かぐや様は告らせたい Vol.1/BD/BDMV/STREAM/00009.m2ts")
src = src[:-24]
ef = bbmod(src, 1, 1, 1, 1, thresh=40, blur=999, y=True, u=False, v=False, scale_thresh=True)
shift = haf.FixChromaBleedingMod(ef, cx=0.5, cy=0, thr=100, strength=1, blur=True)
shift = depth(shift, 32)


scaled = lvf.scale.descale(shift, height=874)

ref = mvf.BM3D(src, sigma=[4, 0], depth=16, profile1="lc")
ref = core.f3kdb.Deband(ref, output_depth=16, range=18, preset="high/luma/nograin")
d_mask = kgf.adaptive_grain(ref, show_mask=True, luma_scaling=24)
l_mask = kgf.retinex_edgemask(ref)
den_mask = depth(core.std.Expr([d_mask, l_mask], "x y +"), 16)

denoise_a = mvf.BM3D(scaled, sigma=[.8, 1], depth=16)
denoise_b = CoolDegrain(scaled, tr=1, thsad=24, thsadc=48, bits=16, blksize=8, overlap=4)
denoise = core.std.MaskedMerge(denoise_a, denoise_b, den_mask)

deband_a = core.f3kdb.Deband(denoise, range=16, output_depth=16, preset="medium/nograin")
deband_b = core.f3kdb.Deband(denoise, range=14, output_depth=16, preset="medium")
denoise = core.std.MaskedMerge(deband_a, deband_b, depth(d_mask, 16))

grain = kgf.adaptive_grain(denoise, 0.2, luma_scaling=6)


out = grain
final = depth(out, 10)
final.set_output()
