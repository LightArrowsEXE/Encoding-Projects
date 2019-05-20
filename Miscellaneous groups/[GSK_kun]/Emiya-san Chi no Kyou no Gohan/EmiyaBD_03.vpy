import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import vsTAAmbk as taa
from nnedi3_rpow2 import nnedi3_rpow2
core = vs.core
core.max_cache_size = 8192

opstart = 1272
edstart = 15826

src = lvf.src(r"BDMV/衛宮さんちの今日のごはん/Vol 1/BDROM/BDMV/STREAM/00003.m2ts")
src = src[24:-24]
src = fvf.Depth(src, 16)
Y, U, V = kgf.split(src)


scaled = kgf.inverse_scale(src, height=855, kernel='bicubic', b=0.25, c=0.5, mask_detail=True)
scaled = fvf.Depth(scaled, 16)
scaled = nnedi3_rpow2(scaled).resize.Spline36(1920, 1080)
scaled = kgf.join([scaled, U, V])

mask = lvf.src(r"EmiyaBD_OP_mask.png").resize.Spline36(format=vs.YUV420P16, matrix_s='709')
aa_a = taa.TAAmbk(scaled, aatype='Eedi3')
aa_b = taa.TAAmbk(scaled, aatype='Eedi3SangNom', cycle=1)
aa_b = core.std.MaskedMerge(aa_a, aa_b, mask)
aa = fvf.rfs(aa_a, aa_b, mappings=f"[{opstart+469} {opstart+480}]")

merge = fvf.rfs(grain, scaled, mappings=f"[{edstart} {edstart+2155}]")


out = merge
final = fvf.Depth(out, 10)
final.set_output()
