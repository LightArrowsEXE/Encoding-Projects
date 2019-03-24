import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import vsTAAmbk as taa
core = vs.core
core.max_cache_size = 8192

src = lvf.src(r"「ペルソナ５ ザ・ロイヤル」ティザーCM-ygyz3Mqjh0k.mkv")
src = src[30:]
src = fvf.Depth(src, 16)

scaled = core.resize.Spline36(src, 1280, 720)

denoise = lvf.qden(scaled, h=0.4)
aa = taa.TAAmbk(denoise, aatype='Eedi3', opencl=True)
deband = core.f3kdb.Deband(aa, range=18, y=48, cb=40, cr=40, grainy=0, grainc=0, output_depth=16)
grain = kgf.adaptive_grain(deband, 0.3)

out = grain
final = fvf.Depth(out, 10)
final.set_output()
