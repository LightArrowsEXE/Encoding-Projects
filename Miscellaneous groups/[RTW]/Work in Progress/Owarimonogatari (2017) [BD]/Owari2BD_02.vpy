import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import vsTAAmbk as taa
import havsfunc as haf
from nnedi3_rpow2 import nnedi3_rpow2
core = vs.core
core.max_cache_size = 8192


opstart = 2398
edstart = 28868

src = lvf.src(r"BDMV/[BDMV][アニメ][171025] 「終物語」 第六巻／まよいヘル/BD_VIDEO/BDMV/STREAM/00002.m2ts")
src = src[:34529]
src = core.edgefixer.ContinuityFixer(src, [4,2,2], [4,2,2], [4,2,2], [4,2,2])
src = fvf.Depth(src, 16)


Y, U, V = kgf.split(src)
scaled = kgf.inverse_scale(src, height=720, kernel='bicubic', b=0, c=1/2, mask_detail=True)
scaled = fvf.Depth(scaled, 16)

denoise_a = lvf.quick_denoise(scaled, h=1, sigma=5)
denoise_b = lvf.quick_denoise(scaled, h=2.4, sigma=8)
denoise_c = lvf.quick_denoise(scaled, h=0.4)
denoise = fvf.rfs(denoise_a, denoise_b, mappings="[12450 12513]")
denoise = fvf.rfs(denoise, denoise_c, mappings="[28286 28867]")
denoise = fvf.rfs(denoise, scaled, mappings="[1384 1431] [1467 1630] [1648 1736] [1822 1872] [1947 2055] [4761 4814] [5035 5175] [5884 6087] [5788 5829] [6088 6123] [6490 6729] [7133 7180] [7279 7359] [7543 7653] [7783 8475] [8548 8613] [9295 9348] [9439 9624] [9685 9828] [10045 10236] [10266 10502] [10839 10958] [11199 11378] [12039 12158] [12591 12842] [13089 13184] [13233 13358] [13800 13871] [13932 13991] [15291 15485] [15529 15568] [16332 16568] [15847 15881] [16002 16031] [16629 16736] [24800 25010]")

aa_a = taa.TAAmbk(denoise, aatype='Nnedi3')
aa_b = taa.TAAmbk(denoise, aatype='Eedi3', opencl=True)
aa_c = taa.TAAmbk(denoise, aatype='Eedi3SangNom')
aa = fvf.rfs(aa_a, aa_b, mappings=f"[{opstart+713} {opstart+880}] [{opstart+905} {opstart+920}] [{edstart+2047} {edstart+2157}] [7654 7731] [7999 8475] [10503 10532] [12514 12590] [13542 13571] [13800 13871] [14505 14606] [18130 18201] [19735 19800] [20110 20145] [26246 26353] [27091 27126]")
aa = fvf.rfs(aa, aa_c, mappings="[16002 16031]")

scaled = nnedi3_rpow2(aa).resize.Spline36(1920, 1080)
scaled = kgf.join([scaled, U, V])

deband_a = core.f3kdb.Deband(scaled, range=18, y=48, cb=40, cr=40, grainy=24, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(scaled, range=21, y=64, cb=56, cr=56, grainy=24, grainc=0, output_depth=16)
deband_c = core.f3kdb.Deband(scaled, range=15, y=32, cb=24, cr=24, grainy=24, grainc=0, output_depth=16)
deband = fvf.rfs(deband_a, deband_b, mappings=f"[{edstart} {edstart+672}] [{edstart+904} {edstart+1332}] [{edstart+1490} {edstart+1758}] [{edstart+2047} {edstart+2157}] ")
deband = fvf.rfs(deband, deband_c, mappings="[12450 12513] [13233 13358] [13800 13871] [28286 28867]")
deband = fvf.rfs(deband, scaled, mappings="[1467 1630] [1648 1736] [9439 9480] [10045 10236] [13089 13184] [15847 15881] [16002 16031] [16629 16736]")

grain_a = kgf.adaptive_grain(deband, 0.5)
grain_b = kgf.adaptive_grain(deband, 2)
grain = fvf.rfs(grain_a, grain_b, mappings=f"[{edstart} {edstart+672}] [{edstart+904} {edstart+1332}] [{edstart+1490} {edstart+1758}] [{edstart+2047} {edstart+2157}]")


out = grain
final = fvf.Depth(out, 10)
final.set_output()
