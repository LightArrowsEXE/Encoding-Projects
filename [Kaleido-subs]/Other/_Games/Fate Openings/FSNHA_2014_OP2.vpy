import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import havsfunc as haf
import vsTAAmbk as taa
core = vs.core
core.max_cache_size = 8192

src = lvf.src(r"src/PCSG00386/image/movie/opening2.mp4")
src = core.std.Crop(src, 0, 0, 2, 2)
src = core.edgefixer.ContinuityFixer(src, [0,0,0], [0,0,0], [2,1,1], [2,1,1])
src = fvf.Depth(src, 16)


denoise_a = lvf.quick_denoise(src, h=0.8, sigma=4)
denoise_b = lvf.quick_denoise(src, h=1.4, sigma=6)
denoise = fvf.rfs(denoise_a, denoise_b, mappings="[319 372]")

deband_a = core.f3kdb.Deband(denoise, range=16, y=32, cb=24, cr=24, grainy=0, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(denoise, range=5, y=120, cb=112, cr=112, grainy=0, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(deband_b, range=16, y=64, cb=56, cr=56, grainy=0, grainc=0, output_depth=16)
deband_c = core.f3kdb.Deband(denoise, range=18, y=48, cb=40, cr=40, grainy=12, grainc=0, output_depth=16)
deband = fvf.rfs(deband_a, deband_b, mappings="[0 64] [1865 1934] [2503 2649]")
deband = fvf.rfs(deband, deband_c, mappings="[294 372]")

sharpen = haf.LSFmod(denoise, strength=60, soft=10, edgemode=1, Smethod=2, Lmode=2)
aa = taa.TAAmbk(sharpen, aatype='Nnedi3')

mask = kgf.retinex_edgemask(src).std.Binarize()
merge = core.std.MaskedMerge(deband, aa, mask)

grain = kgf.adaptive_grain(merge, 0.5)

out = grain
final = fvf.Depth(out, 10)
final.set_output()
