import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import havsfunc as haf
import vsTAAmbk as taa
core = vs.core
core.max_cache_size = 8192

src = lvf.src(r"src/PCSG00386/image/movie/opening.mp4")
src = core.std.Crop(src, 0, 0, 2, 2)
src = core.edgefixer.ContinuityFixer(src, [0,0,0], [0,0,0], [2,1,1], [2,1,1])
src = fvf.Depth(src, 16)


denoise_a = lvf.quick_denoise(src, h=0.8, sigma=4)
deband_a = core.f3kdb.Deband(denoise_a, range=16, y=32, cb=24, cr=24, grainy=0, grainc=0, output_depth=16)
denoise_b = lvf.quick_denoise(src, h=1.4, sigma=6)
deband_b = core.f3kdb.Deband(denoise_b, range=5, y=120, cb=112, cr=112, grainy=0, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(deband_b, range=16, y=64, cb=56, cr=56, grainy=0, grainc=0, output_depth=16)
deband = fvf.rfs(deband_a, deband_b, mappings="[959 1036] [1360 1379]")

sharpen = haf.LSFmod(denoise_a, strength=60, soft=10, edgemode=1, Smethod=2, Lmode=2)
aa = taa.TAAmbk(sharpen, aatype='Nnedi3')

mask = kgf.retinex_edgemask(src).std.Binarize()
merge = core.std.MaskedMerge(deband, aa, mask)

grain_a = kgf.adaptive_grain(merge, 0.3)
grain_b = kgf.adaptive_grain(merge, 0.7)
grain = fvf.rfs(grain_a, grain_b, mappings="[959 1036]")


out = grain
final = fvf.Depth(out, 10)
final.set_output()
