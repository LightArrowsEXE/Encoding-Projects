import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import vsTAAmbk as taa
import havsfunc as haf
core = vs.core
core.max_cache_size = 8192

# PS: FUCK YOUTUBE VIDEOS

src = lvf.src(r"【FGO】Fate_Grand Order☓月姫コラボイベントCM-GpLSFzMUqcc.mp4")
src = fvf.AutoDeblock(src)
src = core.std.AssumeFPS(src, fpsnum=24000, fpsden=1001)
src = fvf.Depth(src, 16)

scaled = core.resize.Spline36(src, 1280, 720)

denoise = lvf.qden(scaled, h=1, sigma=3)

deband_a = core.f3kdb.Deband(denoise, range=15, y=32, cb=24, cr=24, grainy=0, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(denoise, range=21, y=48, cb=40, cr=40, grainy=12, grainc=0, output_depth=16)
deband = fvf.rfs(deband_a, deband_b, mappings="[432 467]")

aa = taa.TAAmbk(scaled, aatype='Eedi3', opencl=True, cycle=1)
darken = haf.FastLineDarkenMOD(aa, strength=72, protection=5, luma_cap=191, threshold=4, thinning=0)

mask = kgf.retinex_edgemask(aa)
maskedmerge = core.std.MaskedMerge(deband, darken, mask)

grain = kgf.adaptive_grain(maskedmerge, 1)
grain = fvf.rfs(maskedmerge, grain, mappings="[667 676] [639 666]")

out = core.sub.TextFile(grain, r"Tsukihime×Fate Grand Order CM [Hardsubbed Signs].ass")
final = fvf.Depth(out, 10)
final.set_output()
