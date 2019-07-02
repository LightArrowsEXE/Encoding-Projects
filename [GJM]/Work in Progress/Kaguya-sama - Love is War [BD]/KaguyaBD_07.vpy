import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import havsfunc as haf
import mvsfunc as mvf
from nnedi3_rpow2 import nnedi3_rpow2
core = vs.core

src = lvf.src(r"BDMV/[BDMV][190626][Kaguya-sama - Love Is War][Vol.4]/BDMV/STREAM/00001.m2ts")
src = src[:34525]
src = core.edgefixer.ContinuityFixer(src, [4,2,2], [4,2,2], [4,2,2], [4,2,2])
src = fvf.Depth(src, 16)
src = haf.FixChromaBleedingMod(src, cx=0.5, cy=0, thr=100, strength=1, blur=True)
Y, U, V = kgf.split(src)

scaled = kgf.inverse_scale(Y, height=874, kernel='bicubic', b=0, c=1/2, mask_detail=True)
scaled = nnedi3_rpow2(scaled).resize.Spline36(1920, 1080, format=vs.YUV420P16)
scaled = kgf.join([scaled, U, V])

denoise = mvf.BM3D(scaled, sigma=[3,0.5])
deband = core.f3kdb.Deband(denoise, range=18, y=32, cb=24, cr=24, grainy=0, grainc=0, output_depth=16)

grain = kgf.adaptive_grain(deband, 0.2, luma_scaling=10)

out = grain
final = fvf.Depth(out, 10)
final.set_output()