import vapoursynth as vs
import fvsfunc as fvf
import kagefunc as kgf
import lvsfunc as lvf
import vsTAAmbk as taa
from nnedi3_rpow2 import nnedi3_rpow2
core = vs.core

opstart, edstart = None, 0


src = lvf.src(r"BDMV/[BDMV][190731][Kimetsu no Yaiba][Vol.1]/BDMV/STREAM/00008.m2ts")
src = src[:2160]
src = fvf.Depth(src, 16)


Y, U, V = kgf.split(src)
scaled = kgf.inverse_scale(Y, height=855, kernel='bicubic', b=1/5, c=2/5, denoise=True, bm3d_sigma=3.5, use_gpu=False)
scaled = fvf.Depth(scaled, 16)

aa_a = taa.TAAmbk(scaled, aatype='Nnedi3')
aa_b = taa.TAAmbk(scaled, aatype='Eedi3')
aa = fvf.rfs(aa_a, aa_b, mappings=f"")

scaled = nnedi3_rpow2(aa).resize.Spline36(src.width, src.height)
scaled = kgf.join([scaled, U, V])

deband_a = core.f3kdb.Deband(scaled, range=17, y=40, cb=32, cr=32, grainy=24, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(scaled, range=20, y=48, cb=40, cr=40, grainy=36, grainc=0, output_depth=16)
deband = fvf.rfs(deband_a, deband_b, mappings=f"[{edstart+1494} {edstart+1600}]")

grain_a = kgf.adaptive_grain(deband, 0.5, luma_scaling=6)
grain_b = kgf.adaptive_grain(deband, 1)
grain_c = core.grain.Add(deband, 10, constant=False)
grain = fvf.rfs(grain_a, grain_b, mappings=f"")
grain = fvf.rfs(grain, grain_c, mappings=f"")


out = grain
final = fvf.Depth(out, 10)
final.set_output()
