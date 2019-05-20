import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
from nnedi3_rpow2 import nnedi3_rpow2
core = vs.core
core.max_cache_size = 8192

src = lvf.src(r"BDMV/衛宮さんちの今日のごはん/Vol 1/BDROM/BDMV/STREAM/00004.m2ts")
src = src[24:2181]
src = fvf.Depth(src, 16)
Y, U, V = kgf.split(src)

scaled = kgf.inverse_scale(src, height=855, kernel='bicubic', b=0.2, c=0.4)
scaled = fvf.Depth(scaled, 16)
scaled = nnedi3_rpow2(scaled).resize.Spline36(1920, 1080)
scaled = kgf.join([scaled, U, V])

out = scaled
final = fvf.Depth(out, 10)
comp = lvf.comp(src, out, [71, 202, 355, 592, 1172, 1290, 1522, 1782, 2011, 2102])
final.set_output()
