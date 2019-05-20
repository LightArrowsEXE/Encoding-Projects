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
epend = 19852

# Note: after cutting
edstart = 13184


src = lvf.src(r"BDMV/[BDMV][190402][マナリアフレンズ II]/BD/BDMV/STREAM/00008.m2ts")
blank = core.std.BlankClip(src) # Part B starts too abruptly, so there's some space for a breather after ED.
src = src[24:preview]+blank[:48]+src[part_b:]+src[preview:part_b]
src = fvf.Depth(src, 16)
Y, U, V = kgf.split(src)

scaled = kgf.inverse_scale(src, height=878, kernel='bicubic', mask_detail=True, masking_areas=[[1187,1453],[edstart,edstart+1124],[18415,18484],[epend-240,epend]])
scaled = nnedi3_rpow2(scaled).resize.Spline36(1920, 1080, format=vs.YUV420P16)
scaled_m = kgf.mask_descale(src, scaled, kernel='bicubic').resize.Spline36(1920, 1080, format=vs.GRAY16)
scaled = core.std.MaskedMerge(scaled, src, scaled_m)
scaled = kgf.join([scaled, U, V])

denoise_a = lvf.qden(scaled, h=0.8, sigma=4)
deband_a = core.f3kdb.Deband(denoise_a, range=17, y=32, cb=24, cr=24, grainy=0, grainc=0, output_depth=16)
denoise_b = lvf.qden(scaled, h=1.8, sigma=6)
deband_b = core.f3kdb.Deband(denoise_b, range=18, y=40, cb=32, cr=32, grainy=0, grainc=0, output_depth=16)
deband = fvf.rfs(deband_a, deband_b, mappings="[12629 13183] [16798 16863] [17290 17385] [17482 17613] [17974 18254] [18415 18750] [18895 19115]")

aa = taa.TAAmbk(scaled, aatype='Eedi3')

mask = kgf.retinex_edgemask(aa, 1)
maskedmerge = core.std.MaskedMerge(deband, aa, mask)

grain_a = kgf.adaptive_grain(maskedmerge, 0.1)
grain_b = kgf.adaptive_grain(maskedmerge, 0.3)
grain = fvf.rfs(grain_a, grain_b, mappings="[12629 13183] [16798 16863] [17290 17385] [17482 17613] [17974 18254] [18415 18750] [18895 19115]")

out = grain
final = fvf.Depth(out, 10)
src.set_output()
