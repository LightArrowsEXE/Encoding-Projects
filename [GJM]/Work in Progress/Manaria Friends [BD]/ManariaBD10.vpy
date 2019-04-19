import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
from nnedi3_rpow2 import nnedi3_rpow2
import vsTAAmbk as taa
core = vs.core
core.max_cache_size = 8192

# Note: before cutting
endcard = 16688
part_b = 16928
epend = 21002

# Note: after cutting
edstart = 13198


src = lvf.src(r"BDMV/[BDMV][190402][マナリアフレンズ II]/BD/BDMV/STREAM/00011.m2ts")
blank = core.std.BlankClip(src) # Part B starts too abruptly, so there's some space for a breather after ED.
src = src[24:endcard]+blank[:48]+src[part_b:]+src[endcard:part_b]
src = fvf.Depth(src, 16)
Y, U, V = kgf.split(src)

scaled = kgf.inverse_scale(src, height=878, kernel='bicubic', mask_detail=True, masking_areas=[[1845,1995],[edstart,edstart+1300],[16408,16669],[epend-240,epend]])
scaled = nnedi3_rpow2(scaled).resize.Spline36(1920, 1080, format=vs.YUV420P16)
scaled_m = kgf.inverse_scale(src, height=878, kernel='bicubic', mask_detail=True, show_mask=True).resize.Spline36(1920, 1080, format=vs.GRAY16)
scaled = core.std.MaskedMerge(scaled, src, scaled_m)
scaled = kgf.join([scaled, U, V])

denoise_a = lvf.qden(scaled, h=0.8, sigma=4)
deband_a = core.f3kdb.Deband(denoise_a, range=17, y=32, cb=24, cr=24, grainy=0, grainc=0, output_depth=16)
denoise_b = lvf.qden(scaled, h=1.6, sigma=7)
deband_b = core.f3kdb.Deband(denoise_b, range=19, y=48, cb=40, cr=40, grainy=0, grainc=0, output_depth=16)
deband = fvf.rfs(deband_a, deband_b, mappings="[18503 18766]")

aa_a = taa.TAAmbk(scaled, aatype='Eedi3')
aa_b = taa.TAAmbk(scaled, aatype='Eedi3SangNom')
aa = fvf.rfs(aa_a, aa_b, mappings="[13053 13173]")

mask = kgf.retinex_edgemask(aa, 1)
maskedmerge = core.std.MaskedMerge(deband, aa, mask)

grain_a = kgf.adaptive_grain(maskedmerge, 0.1)
grain_b = kgf.adaptive_grain(maskedmerge, 0.5)
grain = fvf.rfs(grain_a, grain_b, mappings="[18503 18766]")

out = grain
final = fvf.Depth(out, 10)
final.set_output()
