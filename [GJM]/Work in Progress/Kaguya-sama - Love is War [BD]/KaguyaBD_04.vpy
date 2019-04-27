import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import havsfunc as haf
from nnedi3_rpow2 import nnedi3_rpow2
core = vs.core
core.max_cache_size = 8192

src = lvf.src(r"BDMV/かぐや様は告らせたい Vol.2/BD/BDMV/STREAM/00002.m2ts")
src = src[:34526]
src = core.edgefixer.ContinuityFixer(src, [4,2,2], [4,2,2], [4,2,2], [4,2,2])
src = fvf.Depth(src, 16)
shift = haf.FixChromaBleedingMod(src, cx=0.5, cy=0, thr=100, strength=1, blur=True)
Y, U, V = kgf.split(shift)

scaled = kgf.inverse_scale(src, height=874, kernel='bicubic', a1=0, a2=1/2)
scaled = nnedi3_rpow2(scaled).resize.Spline36(1920, 1080, format=vs.YUV420P16)
scaled = kgf.join([scaled, U, V])

denoise = lvf.qden(scaled, h=0.2, sigma=3)
deband = core.f3kdb.Deband(denoise, range=18, y=32, cb=24, cr=24, grainy=0, grainc=0, output_depth=16)

grain = kgf.adaptive_grain(deband, 0.2, luma_scaling=10)

out = grain
final = fvf.Depth(out, 10)
final.set_output()