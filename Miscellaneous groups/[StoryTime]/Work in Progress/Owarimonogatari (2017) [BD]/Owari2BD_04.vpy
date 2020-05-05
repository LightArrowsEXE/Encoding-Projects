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


opstart = 0
edstart = 27526

src = lvf.src(r"BDMV/[BDMV][アニメ][171129] 「終物語」 第七巻／ひたぎランデブー/BD_VIDEO/BDMV/STREAM/00002.m2ts")
src = src[:34527]
src = core.edgefixer.ContinuityFixer(src, [4,2,2], [4,2,2], [4,2,2], [4,2,2])
src = fvf.Depth(src, 16)


Y, U, V = kgf.split(src)
scaled = kgf.inverse_scale(src, height=720, kernel='bicubic', b=0, c=1/2, mask_detail=True)
scaled = fvf.Depth(scaled, 16)

denoise_a = lvf.quick_denoise(scaled, h=1, sigma=5)
denoise_b = lvf.quick_denoise(scaled, h=2.4, sigma=8)
denoise_c = lvf.quick_denoise(scaled, h=0.4)
denoise = fvf.rfs(denoise_a, denoise_b, mappings="")
denoise = fvf.rfs(denoise, denoise_c, mappings="[13579 13752] [16166 16337] [16407 16521] [17327 17617] [18868 18962] [21310 21357] [21835 21853] [24949 24987] [25605 25718] [25789 25932] [25954 26094] [26119 26172] [26542 26601] [27262 27381]")
denoise = fvf.rfs(denoise, scaled, mappings="[9748 9861] [9997 10008] [10093 10101] [10120 10128] [10221 10226] [10233 10237] [10243 10246] [10251 10254] [10258 10260] [10264 10266] [10270 10272] [10275 10277] [12332 12355] [12690 12725] [15298 15366] [15382 15556] [15596 15715] [15764 15838] [15872 15979] [16850 16906] [17135 17194] [20467 20508] [20725 20856] [22515 22547] [22996 23025] [23306 23322] [23392 23411] [23894 23925] [24389 24698] [24988 25017] [25090 25119] [25183 25389] [25444 25497] [26773 27015] [27382 27525] [32103 32219] [32412 32648] [32667 32714] [32739 32774] [32817 33125] [33186 33372] [33433 33600] [33661 33744] [33769 33976]")

aa_a = taa.TAAmbk(denoise, aatype='Nnedi3')
aa_b = taa.TAAmbk(denoise, aatype='Eedi3', opencl=True)
aa_c = taa.TAAmbk(denoise, aatype='Eedi3SangNom', opencl=True)
aa_d = lvf.NnEedi3(denoise)
aa = fvf.rfs(aa_a, aa_b, mappings=f"[{opstart+834} {opstart+935}] [{opstart+1633} {opstart+1670}] [17387 17485] [17558 17617] [22431 22466] [22682 22885] [23628 23825] [24699 24814] [25789 25932] [25954 26094] [26119 26172] [26431 26499] [26542 26601] [27382 27525] [30639 30686] [30843 30899]")
aa = fvf.rfs(aa, aa_c, mappings="[22614 22651]")
aa = fvf.rfs(aa, aa_d, mappings="[15298 15366] [15764 15838] [15872 15979] [23026 23172]")


scaled = nnedi3_rpow2(aa).resize.Spline36(1920, 1080)
scaled = kgf.join([scaled, U, V])
scaled = fvf.rfs(scaled, src, mappings="[2261 2342] [2397 2651] [2676 2859] [2890 3375] [3424 3495] [3594 4010] [4081 4461] [4529 4613] [4641 4759] [4777 4860] [5083 5791] [5918 6121] [6140 6211] [6239 6274] [6330 6383] [6459 6482] [6533 6812] [6919 6999] [7036 7164] [7189 7488] [7648 7773] [7800 7819] [7879 7948] [8083 8547] [8788 8880] [8923 9144] [9169 9324] [9406 9702] [10081 10092] [10147 10220] [10339 10392] [10423 10863] [10888 11145] [11164 11391] [11437 11634] [11695 11757] [11812 12288] [12306 12331] [12509 12613] [12993 13142] [13251 13578] [13753 14010] [17021 17080]")

denoise_us = lvf.quick_denoise(scaled, h=0.6, sigma=4)
denoise_us = fvf.rfs(scaled, denoise_us, mappings="[12509 12664] [12993 13142] [13251 13578] [13753 14010] [16076 16123] [17021 17080]")

aa_us = taa.TAAmbk(denoise_us, aatype='Eedi3', opencl=True)
aa_us = fvf.rfs(denoise_us, aa_us, mappings="[2261 2342] [2397 2651] [2676 2859] [2890 3375] [3424 3495] [3594 4010] [4081 4461] [4529 4613] [4641 4759] [4777 4860] [5083 5791] [5918 6121] [6140 6211] [6239 6274] [6330 6383] [6459 6482] [6533 6812] [6919 6999] [7036 7164] [7189 7488] [7648 7773] [7800 7819] [7879 7948] [8083 8547] [8788 8880] [8923 9144] [9169 9324] [9406 9702] [10081 10092] [10147 10220] [10339 10392] [10423 10863] [10888 11145] [11164 11391] [11437 11634] [11695 11757] [11812 12288] [12306 12331] [12509 12613] [12993 13142] [13251 13578] [13753 14010] [16076 16123] [17021 17080]")

deband_a = core.f3kdb.Deband(aa_us, range=18, y=48, cb=40, cr=40, grainy=24, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(aa_us, range=21, y=64, cb=56, cr=56, grainy=24, grainc=0, output_depth=16)
deband_c = core.f3kdb.Deband(aa_us, range=15, y=32, cb=24, cr=24, grainy=24, grainc=0, output_depth=16)
deband = fvf.rfs(deband_a, deband_b, mappings=f"[{edstart} {edstart+672}] [{edstart+904} {edstart+1332}] [{edstart+1490} {edstart+1758}] [{edstart+2047} {edstart+2157}] [16850 16906]")
deband = fvf.rfs(deband, deband_c, mappings="[16076 16123] [16166 16337] [21835 21853] [24389 24698] [24988 25017] [25090 25119] [32103 32219] [32412 32648] [32667 32714] [32739 32774] [32817 32996] [33186 33372] [33433 33600] [33661 33744] [33769 33976]")
deband = fvf.rfs(deband, aa_us, mappings="[15298 15366] [15596 15715] [15764 15838] [15872 15979] [17327 17617] [20467 20508] [20725 20856] [21310 21357] [22515 22547] [22996 23025] [23306 23322] [23392 23411] [23894 23925] [25789 25932] [25954 26094] [26119 26172] [26542 26601] [26773 27015] [27382 27525] [32997 33125]")

grain_a = kgf.adaptive_grain(deband, 0.5)
grain_b = kgf.adaptive_grain(deband, 2)
grain_c = kgf.adaptive_grain(deband, 3, static=False)
grain = fvf.rfs(grain_a, grain_b, mappings=f"[{edstart} {edstart+672}] [{edstart+904} {edstart+1332}] [{edstart+1490} {edstart+1758}] [{edstart+2047} {edstart+2157}]")
grain = fvf.rfs(grain, grain_c, mappings="[14599 14631] [32085 32102] [34003 34020]")


out = grain
final = fvf.Depth(out, 10)
final.set_output()
