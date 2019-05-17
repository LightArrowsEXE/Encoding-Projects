import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import vsTAAmbk as taa
from nnedi3_rpow2 import nnedi3_rpow2
core = vs.core
core.max_cache_size = 8192

opstart = 0

src = lvf.src(r"BDMV/衛宮さんちの今日のごはん/Vol 1/BDROM/BDMV/STREAM/00006.m2ts")
src = src[24:1462]
src = fvf.Depth(src, 16)
Y, U, V = kgf.split(src)

scaled = kgf.inverse_scale(src, height=855, kernel='bicubic', a1=0.2, a2=0.4)
scaled = fvf.Depth(scaled, 16)
scaled = nnedi3_rpow2(scaled).resize.Spline36(1920, 1080)
scaled = kgf.join([scaled, U, V])

mask = lvf.src(r"EmiyaBD_NCOP1 mask.png").resize.Spline36(format=vs.YUV420P16, matrix_s='709')
aa_a = taa.TAAmbk(scaled, aatype='Eedi3')
aa_b = taa.TAAmbk(scaled, aatype='Eedi3SangNom', cycle=1)
aa_b = core.std.MaskedMerge(aa_a, aa_b, mask)
aa = fvf.rfs(aa_a, aa_b, mappings=f"[{opstart+469} {opstart+480}]")

out = aa
final = fvf.Depth(out, 10)
final.set_output()
