import vapoursynth as vs
import fvsfunc as fvf
import vsTAAmbk as taa
import kagefunc as kgf
import lvsfunc as lvf
core = vs.core
core.max_cache_size = 8192

src = r"F:\Convert\[BDMV][180926][Gundam Build Divers][BD-BOX1]\GUNDAM_BUILD_DIVERS_BDBOX1_D3\BDMV\STREAM\00011.m2ts"
src = core.lsmas.LWLibavSource(src)
src = src[24:2184]
src = core.edgefixer.ContinuityFixer(src, left=[2,1,1],top=[2,1,1],bottom=[2,1,1], right=[2,1,1])

scaled_a = core.resize.Spline36(src, 1280, 720, format=vs.YUV444P16) #For two scenes that couldn't be reliably descaled
scaled_b = kgf.inverse_scale(src, height=720, kernel='spline36')
scaled_b = fvf.Depth(scaled_b, 16)
scaled = core.remap.Rfs(scaled_b, scaled_a, mappings="[0 223] [1603 1639]") 

denoised = lvf.denoise(scaled, h=0.8, radius=3)
denoised = core.remap.Rfs(denoised, scaled, mappings="[1056 1135] [1311 1366] [1653 1672]")

mask = kgf.retinex_edgemask(scaled, sigma=1).std.Binarize()
masked = core.std.MaskedMerge(denoised, scaled, mask)

deband_a = core.f3kdb.Deband(masked, range=14, y=48, cb=40, cr=40, grainy=0, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(masked, range=18, y=72, cb=64, cr=64, grainy=12, grainc=0, output_depth=16)
deband = core.remap.Rfs(deband_a, deband_b, mappings="[314 350]")

out = deband
final = fvf.Depth(out, 10)
final.set_output()
