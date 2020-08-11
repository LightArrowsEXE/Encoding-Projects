import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import vsTAAmbk as taa
import havsfunc as haf
core = vs.core
core.max_cache_size = 8192

src = lvf.src(r"../アニメ「マンガでわかる！Fate_Grand Order」-98s0s3VWwho.mkv")
src = src[:8032]
src = fvf.Depth(src, 16)
scaled = core.resize.Bicubic(src, 1280, 720)

# fuck YT sources tbh
denoise_a = lvf.qden(scaled, h=0.4, sigma=2)
denoise_b = lvf.qden(scaled, h=0.8, sigma=4)
deband_a = core.f3kdb.Deband(denoise_a, range=15, y=32, cb=24, cr=24, grainy=0, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(denoise_a, range=18, y=48, cb=40, cr=40, grainy=0, grainc=0, output_depth=16)
deband_c = core.f3kdb.Deband(denoise_a, range=21, y=64, cb=56, cr=56, grainy=0, grainc=0, output_depth=16)
deband_d = core.f3kdb.Deband(denoise_b, range=5, y=72, cb=64, cr=64, grainy=0, grainc=0, output_depth=16)
deband_d = core.f3kdb.Deband(deband_d, range=18, y=40, cb=32, cr=32, grainy=12, grainc=0, output_depth=16)
deband = fvf.rfs(deband_a, deband_b, mappings="[0 268] [3036 3163]")
deband = fvf.rfs(deband, deband_c, mappings="[4770 5033] [5143 5430]")
deband = fvf.rfs(deband, deband_d, mappings="[795 884]")

sharpen = haf.LSFmod(scaled, strength=80, soft=-2, edgemode=1, Smethod=2, preblur=True)
aa = taa.TAAmbk(sharpen, aatype='Eedi3', opencl=True)

mask = kgf.retinex_edgemask(aa, 1)
maskedmerge = core.std.MaskedMerge(deband, aa, mask)

grain_a = kgf.adaptive_grain(maskedmerge, 0.1)
grain_b = kgf.adaptive_grain(maskedmerge, 0.3)
grain = fvf.rfs(grain_a, grain_b, mappings="[795 884]")

out = grain
final = fvf.Depth(out, 10)
comp = lvf.comp(scaled, out, [39, 91, 109, 268, 716, 795, 943, 1330, 1331, 1572, 1573, 1580, 1595, 3131, 3403, 4118, 5033, 5034, 5143, 5464, 6033, 6034, 7192, 7437, 7671])
final.set_output()