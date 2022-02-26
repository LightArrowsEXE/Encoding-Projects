import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import vsTAAmbk as taa
from nnedi3_rpow2 import nnedi3_rpow2
core = vs.core
core.max_cache_size = 8192


edstart = 0

src = lvf.src(r"BDMV/[BDMV][アニメ][171025] 「終物語」 第六巻／まよいヘル/BD_VIDEO/BDMV/STREAM/00010.m2ts")
src = src[12:-24]
src = core.edgefixer.ContinuityFixer(src, [4,2,2], [4,2,2], [4,2,2], [4,2,2])
src = fvf.Depth(src, 16)


Y, U, V = kgf.split(src)
scaled = kgf.inverse_scale(src, width=None, height=720, kernel='bicubic', b=0, c=1/2, mask_detail=True)
scaled = fvf.Depth(scaled, 16)

denoise = lvf.quick_denoise(scaled, h=1, sigma=5)
aa = taa.TAAmbk(denoise, aatype='Eedi3', opencl=True)
aa = fvf.rfs(denoise, aa, mappings=f"[{edstart+2047} {edstart+2157}]")

scaled = nnedi3_rpow2(aa).resize.Spline36(1920, 1080)
scaled = kgf.join([scaled, U, V])

deband_a = core.f3kdb.Deband(scaled, range=18, y=48, cb=40, cr=40, grainy=24, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(scaled, range=24, y=64, cb=56, cr=56, grainy=24, grainc=0, output_depth=16)
deband = fvf.rfs(deband_a, deband_b, mappings=f"[{edstart} {edstart+672}] [{edstart+904} {edstart+1332}] [{edstart+1490} {edstart+1758}] [{edstart+2047} {edstart+2157}]")

grain_a = kgf.adaptive_grain(deband, 0.5)
grain_b = kgf.adaptive_grain(deband, 2)
grain = fvf.rfs(grain_a, grain_b, mappings=f"[{edstart} {edstart+672}] [{edstart+904} {edstart+1332}] [{edstart+1490} {edstart+1758}] [{edstart+2047} {edstart+2157}]")


out = grain
final = fvf.Depth(out, 10)
final.set_output()
