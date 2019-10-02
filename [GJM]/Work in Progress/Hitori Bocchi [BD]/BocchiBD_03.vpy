import vapoursynth as vs
import fvsfunc as fvf
import kagefunc as kgf
import lvsfunc as lvf
import mvsfunc as mvf
from vsTAAmbk import TAAmbk
from vsutil import get_w
core = vs.core


src = lvf.src(r"G:/src/[BDMV][190724][Hitoribocchi no Marumaru Seikatsu][Vol.1]/BDMV/STREAM/00008.m2ts")
src = core.edgefixer.ContinuityFixer(src, 1, 1, 1, 1, 2)
src = src[24:-24]
src = fvf.Depth(src, 16)

scaled = kgf.inverse_scale(src, height=810, 
                           kernel='bicubic', b=0, c=1,
                           mask_detail=True)
scaled = fvf.Depth(scaled, 16)

mask = kgf.adaptive_grain(scaled, show_mask=True, luma_scaling=2)
denoise_a = mvf.BM3D(scaled, sigma=[4,0])
denoise_b = mvf.BM3D(scaled, sigma=[1.5,0])
denoise = core.std.MaskedMerge(denoise_a, denoise_b, mask)

aa = TAAmbk(denoise, aatype='Eedi3', repair=2)

deband = core.f3kdb.Deband(aa, range=16, y=24, cb=16, cr=16, grainy=24, grainc=0, output_depth=16)
grain = kgf.adaptive_grain(deband, 0.1, luma_scaling=6)


out = grain
final = fvf.Depth(out, 10)
final.set_output()
