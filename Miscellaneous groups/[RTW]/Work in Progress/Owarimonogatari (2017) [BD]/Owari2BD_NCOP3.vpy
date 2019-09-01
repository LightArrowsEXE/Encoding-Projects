import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import vsTAAmbk as taa
from nnedi3_rpow2 import nnedi3_rpow2
import havsfunc as haf
core = vs.core
core.max_cache_size = 8192


opstart = 0

src = lvf.src(r"BDMV/[BDMV][アニメ][171227] 「終物語」 第八巻／おうぎダーク/BD_VIDEO/BDMV/STREAM/00010.m2ts")
src = src[12:-24]
src = core.edgefixer.ContinuityFixer(src, [4,2,2], [4,2,2], [4,2,2], [4,2,2])
src = fvf.Depth(src, 16)


Y, U, V = kgf.split(src)
scaled = kgf.inverse_scale(src, width=None, height=720, kernel='bicubic', b=0, c=1/2, mask_detail=True)
scaled = fvf.Depth(scaled, 16)

denoise = mvf.BM3D(scaled, sigma=[5,2])
denoise = fvf.rfs(denoise, scaled, mappings=f"[{opstart+997} {opstart+1057}] [{opstart+1345} {opstart+1710}]")

aa_a = taa.TAAmbk(denoise, aatype='Nnedi3')
aa_b = taa.TAAmbk(denoise, aatype='Eedi3', opencl=True)
aa = fvf.rfs(aa_a, aa_b, mappings=f"[{opstart} {opstart+428}] [{opstart+2076} {opstart+2131}]")

scaled = nnedi3_rpow2(aa).resize.Spline36(1920, 1080)
scaled = kgf.join([scaled, U, V])

sharpen = haf.LSFmod(scaled, strength=140, soft=10, edgemode=1, Smethod=2, Lmode=2)
darken = haf.FastLineDarkenMOD(sharpen, strength=48, protection=5, luma_cap=191, threshold=4, thinning=0)

dn2 = core.knlm.KNLMeansCL(scaled, a=2, h=0.4, d=3)
db3 = core.bilateral.Bilateral(dn2, sigmaS=1.0, sigmaR=0.02)
mask = kgf.retinex_edgemask(src, 3)
db3m = core.std.MaskedMerge(db3, darken, mask)
db3m = fvf.rfs(scaled, db3m, mappings=f"[{opstart} {opstart+996}] [{opstart+1058} {opstart+1344}] [{opstart+1711} {opstart+2159}]")

deband = core.f3kdb.Deband(db3m, range=18, y=48, cb=40, cr=40, grainy=24, grainc=0, output_depth=16)
grain = kgf.adaptive_grain(deband, 0.5)


out = grain
final = fvf.Depth(out, 10)
final.set_output()
