import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import vsTAAmbk as taa
import havsfunc as haf
from nnedi3_rpow2 import nnedi3_rpow2
core = vs.core
core.max_cache_size = 8192


opstart = 2590
edstart = 32371

src = lvf.src(r"BDMV/[BDMV][アニメ][171025] 「終物語」 第六巻／まよいヘル/BD_VIDEO/BDMV/STREAM/00001.m2ts")
src = src[:-60]
src = core.edgefixer.ContinuityFixer(src, [4,2,2], [4,2,2], [4,2,2], [4,2,2])
src = fvf.Depth(src, 16)


Y, U, V = kgf.split(src)
scaled = kgf.inverse_scale(src, height=720, kernel='bicubic', b=0, c=1/2, mask_detail=True)
scaled = fvf.Depth(scaled, 16)

denoise_a = lvf.quick_denoise(scaled, h=1, sigma=5)
denoise_b = lvf.quick_denoise(scaled, h=2.4, sigma=8)
denoise = fvf.rfs(denoise_a, denoise_b, mappings="[19020 20034] [26215 26244] [27934 27987]")
denoise = fvf.rfs(denoise, scaled, mappings="[7076 7111] [7418 7483] [15293 15406] [18852 19019] [20274 20333] [20487 20540] [20817 20888] [23370 23492]")

aa_a = taa.TAAmbk(denoise, aatype='Nnedi3')
aa_b = taa.TAAmbk(denoise, aatype='Eedi3', opencl=True)
aa_c = taa.TAAmbk(denoise, aatype='Eedi3SangNom')
aa = fvf.rfs(aa_a, aa_b, mappings=f"[{opstart+713} {opstart+880}] [{opstart+905} {opstart+920}] [{edstart+2047} {edstart+2157}] [6301 6342] [7826 7927] [13562 13763] [13794 13831] [14063 14236] [14648 14833] [18045 18060] [20148 20237]")
aa = fvf.rfs(aa, aa_c, mappings="[12988 13011]")

scaled = nnedi3_rpow2(aa).resize.Spline36(1920, 1080)
scaled = kgf.join([scaled, U, V])

deband_a = core.f3kdb.Deband(scaled, range=18, y=48, cb=40, cr=40, grainy=24, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(scaled, range=21, y=64, cb=56, cr=56, grainy=24, grainc=0, output_depth=16)
deband_c = core.f3kdb.Deband(scaled, range=15, y=32, cb=24, cr=24, grainy=24, grainc=0, output_depth=16)
deband_d = core.f3kdb.Deband(scaled, range=24, y=64, cb=56, cr=56, grainy=24, grainc=0, output_depth=16)
deband = fvf.rfs(deband_a, deband_b, mappings=f"[{edstart} {edstart+672}] [{edstart+904} {edstart+1332}] [{edstart+1490} {edstart+1758}] [{edstart+2047} {edstart+2157}] [6487 6585] [7532 7579] [8162 8210] [8588 8641] [26215 26244] [27934 27987]")
deband = fvf.rfs(deband, deband_c, mappings="[6678 6716] [7418 7483] [7826 7879]")
deband = fvf.rfs(deband, deband_d, mappings="[18852 20034]")
deband = fvf.rfs(deband, scaled, mappings="[7076 7111]")

grain_a = kgf.adaptive_grain(deband, 0.5)
grain_b = kgf.adaptive_grain(deband, 2)
grain_c = core.grain.Add(deband, var=1, uvar=0)
grain = fvf.rfs(grain_a, grain_b, mappings=f"[{edstart} {edstart+672}] [{edstart+904} {edstart+1332}] [{edstart+1490} {edstart+1758}] [{edstart+2047} {edstart+2157}] [5944 5991] [6678 6716] [7076 7111] [7418 7483] [8036 8059] [10391 10414] [15648 15687] [18852 19019] [25919 25980]")
grain = fvf.rfs(grain, grain_c, mappings="[8588 8641] [8693 8773]")


out = grain
final = fvf.Depth(out, 10)
final.set_output()
