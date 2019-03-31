import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
from nnedi3_rpow2 import nnedi3_rpow2
import vsTAAmbk as taa
core = vs.core
core.max_cache_size = 8192

# Note: before cutting
preview = 16688
endcard = 16808
part_b = 16928
epend = 19874

# Note: after cutting
edstart = 15586


src = lvf.src(r"BDMV/[BDMV][190302][マナリアフレンズ I]/BD/BDMV/STREAM/00011.m2ts")
blank = core.std.BlankClip(src) # Part B starts too abruptly, so there's some space for a breather after ED.
src = src[24:preview]+blank[:48]+src[part_b:]+src[preview:part_b]
src = fvf.Depth(src, 16)
Y, U, V = kgf.split(src)

scaled = kgf.inverse_scale(src, height=878, kernel='bicubic', mask_detail=True, masking_areas=[[1866,2172],[edstart,edstart+1124],[epend-240,epend]])
scaled = nnedi3_rpow2(scaled).resize.Spline36(1920, 1080, format=vs.YUV420P16)
scaled_m = kgf.inverse_scale(src, height=878, kernel='bicubic', mask_detail=True, show_mask=True).resize.Spline36(1920, 1080, format=vs.GRAY16)
scaled = core.std.MaskedMerge(scaled, src, scaled_m)
scaled = kgf.join([scaled, U, V])

denoise = lvf.qden(scaled, h=0.8, sigma=4)
deband = core.f3kdb.Deband(denoise, range=17, y=32, cb=24, cr=24, grainy=0, grainc=0, output_depth=16)

aa = taa.TAAmbk(scaled, aatype='Eedi3', opencl=True)

mask = kgf.retinex_edgemask(aa, 1)
maskedmerge = core.std.MaskedMerge(deband, aa, mask)

grain = kgf.adaptive_grain(maskedmerge, 0.1)

out = grain
final = fvf.Depth(out, 10)
final.set_output()
