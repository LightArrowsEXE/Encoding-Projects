import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import vsTAAmbk as taa
from nnedi3_rpow2 import nnedi3_rpow2
core = vs.core
core.max_cache_size = 8192

opstart = 0

src = lvf.src(r"01/Demon Slayer Kimetsu no Yaiba E01 [1080p][AAC][JapDub][GerSub][Web-DL].mp4")
src = src[30449:32606]
src = fvf.Depth(src, 16)
Y, U, V = kgf.split(src)

scaled = kgf.inverse_scale(src, height=855, kernel='bicubic', a1=0.2, a2=0.5)
scaled = nnedi3_rpow2(src).resize.Spline36(1920, 1080)
scaled = kgf.join([scaled, U, V])

aa = taa.TAAmbk(scaled, aatype='Eedi3', opencl=True)
aa = fvf.rfs(scaled, aa, mappings=f"[{opstart+292} {opstart+402}] [{opstart+1017} {opstart+1079}] [{opstart+1701} {opstart+1782}][{opstart+1895} {opstart+1953}]")

denoise = lvf.quick_denoise(aa, h=0.8, sigma=4)
denoise = fvf.rfs(aa, denoise, mappings=f"[{opstart} {opstart+404}] [{opstart+1017} {opstart+1079}] [{opstart+1128} {opstart+1287}] [{opstart+1320} {opstart+1398}]")

deband_a = core.f3kdb.Deband(denoise, range=18, y=40, cb=32, cr=32, grainy=12, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(denoise, range=21, y=48, cb=40, cr=40, grainy=12, grainc=0, output_depth=16)
deband = fvf.rfs(deband_a, deband_b, mappings=f"[{opstart+1128} {opstart+1287}]")

grain_a = kgf.adaptive_grain(deband, 0.3)
grain_b = kgf.adaptive_grain(deband, 1)
grain = fvf.rfs(grain_a, grain_b, mappings=f"[{opstart+1128} {opstart+1287}]")

out = grain
final = fvf.Depth(out, 10)
final.set_output()
