import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import vsTAAmbk as taa
import havsfunc as haf
from nnedi3_rpow2 import nnedi3_rpow2
import vsutil
core = vs.core
core.max_cache_size = 8192


opstart = 2638
edstart = 32370

src = lvf.src(r"BDMV/[BDMV][アニメ][171129] 「終物語」 第七巻／ひたぎランデブー/BD_VIDEO/BDMV/STREAM/00001.m2ts")
src = src[:34528]
src = core.edgefixer.ContinuityFixer(src, [4,2,2], [4,2,2], [4,2,2], [4,2,2])
src = fvf.Depth(src, 16)

fix_frame_1 = lvf.src(r"Owari2BD_03_fix_frame.png", fpsnum=24000, fpsden=1001).resize.Point(format=vs.YUV420P16, matrix_s='709')

src = kgf.insert_clip(src, fix_frame_1[0], 28881)

Y, U, V = kgf.split(src)
scaled = kgf.inverse_scale(src, height=720, kernel='bicubic', b=0, c=1/2, mask_detail=True)
scaled = fvf.Depth(scaled, 16)

denoise_a = lvf.quick_denoise(scaled, h=1, sigma=5)
denoise_b = lvf.quick_denoise(scaled, h=2.4, sigma=8)
denoise_c = lvf.quick_denoise(scaled, h=0.4)
denoise = fvf.rfs(denoise_a, denoise_b, mappings="[2506 2637]")
denoise = fvf.rfs(denoise, denoise_c, mappings="[1235 1282] [8123 8170] [25684 25721] [30072 30287] [30942 31025] [31218 31547] [31716 31871]")
denoise = fvf.rfs(denoise, scaled, mappings="[24 113] [2179 2394] [4991 5074] [5327 5374] [5462 5749] [6148 6414] [6799 6834] [6880 6887] [6988 7053] [7238 7285] [7658 7915] [7478 7519] [7562 7597] [8768 9007] [9525 9656] [9843 9914] [10940 10987] [14311 14643] [15889 15916] [20291 20464] [20942 21053] [21996 22031] [22104 22196] [22791 22826] [25134 25169] [25234 25281] [25684 25721] [26220 26379] [28409 28456] [29748 29771] [29301 29360] [29772 29963] [30378 30605] [31026 31073] [31668 31715] [31872 32015] [32076 32278]")

aa_a = taa.TAAmbk(denoise, aatype='Nnedi3')
aa_b = taa.TAAmbk(denoise, aatype='Eedi3', opencl=True)
aa_c = taa.TAAmbk(denoise, aatype='Eedi3SangNom', opencl=True)
aa_d = lvf.NnEedi3(denoise)
aa = fvf.rfs(aa_a, aa_b, mappings=f"[{opstart+834} {opstart+935}] [{opstart+1633} {opstart+1670}] [{edstart+2047} {edstart+2157}] [1927 2094] [2179 2394] [5771 5853] [8366 8383] [12347 12406] [13435 13506] [14284 14310] [15842 15850] [21343 21396] [21420 21438] [21463 21483] [21538 21564] [21580 21596] [21865 21908] [22197 22250] [22350 22502] [22575 22730] [21954 21995] [22197 22250] [23783 23872] [24344 24472] [25050 25109] [26356 26379] [29664 29750] [29772 29963]")
aa = fvf.rfs(aa, aa_c, mappings="[6844 6852] [19901 19942] [20039 20050] [20063 20068] [24344 24367] [27725 27850] [27875 27910]")
aa = fvf.rfs(aa, aa_d, mappings="[1504 1530] [7478 7519]")
aa = fvf.rfs(aa, denoise, mappings="[23115 23150] [23223 23249]")

scaled = nnedi3_rpow2(aa).resize.Spline36(1920, 1080)
scaled = kgf.join([scaled, U, V])
scaled = fvf.rfs(scaled, src, mappings="[30378 30605] [31026 31073]")

deband_a = core.f3kdb.Deband(scaled, range=18, y=48, cb=40, cr=40, grainy=24, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(scaled, range=21, y=64, cb=56, cr=56, grainy=24, grainc=0, output_depth=16)
deband_c = core.f3kdb.Deband(scaled, range=15, y=32, cb=24, cr=24, grainy=24, grainc=0, output_depth=16)
deband = fvf.rfs(deband_a, deband_b, mappings=f"[{edstart} {edstart+672}] [{edstart+904} {edstart+1332}] [{edstart+1490} {edstart+1758}] [{edstart+2047} {edstart+2157}]")
deband = fvf.rfs(deband, deband_c, mappings="[2506 2637] [2179 2394] [7238 7285] [8123 8170] [10940 10987] [20942 21053] [25134 25169] [25234 25281] [30072 30287] [30942 31025] [31026 31073] [31716 31871] [32076 32278]")
deband = fvf.rfs(deband, scaled, mappings="[20291 20464] [20681 20941] [22791 22826] [25684 25721]")

# Thanks Lypheo!
mask = lvf.src(r"Owari2BD_03_mask.png", fpsnum=24000, fpsden=1001).resize.Point(format=vs.GRAYS, matrix_s="709")*src.num_frames
y = vsutil.get_y(src).resize.Bicubic(format=vs.GRAYS)
diff = core.std.Expr([y[25684]*src.num_frames, y], "x y - abs 0.025 > 1 0 ?")
mask = core.std.Expr([mask, diff], "y 1 = 0 x ?").std.Binarize()
mask = fvf.Depth(mask, 16)

# Thanks k3!
dn2 = core.knlm.KNLMeansCL(src, a=2, h=0.85, d=3)

db3 = core.bilateral.Bilateral(dn2, sigmaS=3.0, sigmaR=0.02)
db3g = core.grain.Add(db3, var=1, seed=9001, constant=False)
db3gm = core.std.MaskedMerge(dn2, db3g, mask)

merge = fvf.rfs(deband, db3gm, mappings="[25684 25721]")

grain_a = kgf.adaptive_grain(merge, 0.5)
grain_b = kgf.adaptive_grain(merge, 2)
grain_c = kgf.adaptive_grain(merge, 0.5, static=False)
grain = fvf.rfs(grain_a, grain_b, mappings=f"[{edstart} {edstart+672}] [{edstart+904} {edstart+1332}] [{edstart+1490} {edstart+1758}] [{edstart+2047} {edstart+2157}] [25684 25721]")
grain = fvf.rfs(grain_a, grain_c, mappings="[32328 32369]")
grain = fvf.rfs(grain, scaled, mappings="[22791 22826] [30378 30605]")

out = grain
final = fvf.Depth(out, 10)
final.set_output()
