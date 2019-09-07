import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import mvsfunc as mvf
from nnedi3_rpow2 import nnedi3_rpow2
core = vs.core


src = lvf.src(r"BDMV/かぐや様は告らせたい Vol.1/BD/BDMV/STREAM/00009.m2ts")
src = src[:2208]
src = core.edgefixer.ContinuityFixer(src, [4,2,2], [4,2,2], [4,2,2], [4,2,2])
src = fvf.Depth(src, 16)
Y, U, V = kgf.split(src)

scaled = kgf.inverse_scale(Y, height=874, kernel='bicubic', b=0, c=1/2)
scaled = nnedi3_rpow2(scaled).resize.Spline36(1920, 1080, format=vs.YUV420P16)
scaled = kgf.join([scaled, U, V])

denoise = mvf.BM3D(scaled, sigma=[3,0.5])
deband = core.f3kdb.Deband(denoise, range=19, y=40, cb=32, cr=32, grainy=0, grainc=0, output_depth=16)

grain = kgf.adaptive_grain(deband, 0.1)

out = grain
final = fvf.Depth(out, 10)
final.set_output()
