import vapoursynth as vs
import adjust
import lvsfunc as lvf
import fvsfunc as fvf
import vsTAAmbk as taa
import kagefunc as kgf
core = vs.core
core.max_cache_size = 8192

opstart = 65815

src = lvf.src(r"[Erai-raws] Tate no Yuusha no Nariagari - 01 [1080p][Multiple Subtitle].mkv")
src = fvf.Depth(src, 16)

scaled = core.std.CropRel(src, 2, 2, 0, 0)
scaled = core.resize.Spline36(scaled, 1920, 1080)

warp = core.warp.AWarpSharp2(scaled, thresh=96, chroma=1)
warp = fvf.rfs(scaled, warp, mappings="[96 178] [274 344] [416 469] [512 582] [781 845] [1061 1233] [1823 1965] [1966 2018] [2102 2294] [4193 4247] [6030 6287] [7205 7257] [13271 13462] [16641 16769] [45925 45927] [64067 64209]")

aa_1 = taa.TAAmbk(warp, aatype='Eedi3', opencl=True)
aa_2 = taa.TAAmbk(warp, aatype='Nnedi3', opencl=True)
aa_3 = taa.TAAmbk(warp, aatype='Eedi3', opencl=True, cycle=3)

dbn_1 = core.f3kdb.Deband(aa_1, range=17, y=48, cb=40, cr=40, grainy=24, grainc=0, output_depth=16)
dbn_2 = core.f3kdb.Deband(aa_2, range=21, y=56, cb=48, cr=48, grainy=24, grainc=0, output_depth=16)
dbn_3 = core.f3kdb.Deband(aa_3, range=21, y=56, cb=48, cr=48, grainy=24, grainc=0, output_depth=16)
dbn_4 = core.f3kdb.Deband(aa_1, range=21, y=56, cb=48, cr=48, grainy=24, grainc=0, output_depth=16)
dbn_5 = core.f3kdb.Deband(aa_3, range=17, y=48, cb=40, cr=40, grainy=12, grainc=0, output_depth=16)
dbn = fvf.rfs(dbn_1, dbn_2, mappings="[1483 1583] [4319 4375] [4685 4818] [8946 9404] [9517 9666] [11011 11281] [11450 11578]")
dbn = fvf.rfs(dbn, dbn_3, mappings="[8292 8353] [8354 8770] [8887 8945] [12628 12727] [11723 13038] [15689 15994] [17470 17638] [26091 26157] [31210 31310] [64067 64209]")
dbn = fvf.rfs(dbn, dbn_4, mappings="[17263 17469] [18552 18712] [29862 30040] [43001 43161] [54904 55035] [57066 57161] [58366 58413] [59171 59195] [60630 60757] [61494 61528] [61841 61911] [62570 62652] [65601 65647]")
dbn = fvf.rfs(dbn, dbn_5, mappings="[17950 18197] [22821 23030] [24416 24493] [62909 62985]")
dbn = fvf.rfs(dbn, aa_1, mappings="[1966 2018] [2848 2884] [3047 3249]")
dbn = fvf.rfs(dbn, aa_2, mappings="[8127 8291]")
dbn = fvf.rfs(dbn, aa_3, mappings="[1772 1822] [5081 5146] [5779 5862] [7974 8126] [45925 45927]")
dbn = fvf.rfs(dbn, scaled, mappings="[2372 2465] [4046 4093] [4115 4137] [4149 4179] [4819 5080] [7258 7377] [9810 11010] [13463 13624] [14847 15062] [15211 15538] [16897 17041] [19995 20063] [21473 21904] [23672 23874] [24162 24268] [24708 24766] [25718 25878] [26022 26058] [26708 26820] [30185 30211] [34839 34928] [41063 41117] [46340 46590] [47555 47749] [49777 49930] [51333 51395] [52528 52559] [53515 53620] [53680 53763] [53836 53960] [53985 54140] [54239 54285] [56643 56713] [57161 57227] [57334 57382] [57415 57640] [58279 58365] [58414 58460] [59196 59232] [59519 59748] [60192 60257] [61018 61064] [61529 61623] [62986 63062] [64381 64626] [64985 65325]")

dimming = adjust.Tweak(dbn, sat=1.5, cont=1.5)
dimming_a = adjust.Tweak(dbn, sat=1.1, cont=1.1)
dimming_b = adjust.Tweak(dbn, sat=1.3, cont=1.3)
dimming_c = adjust.Tweak(dbn, sat=1.45, cont=1.45)
dimming_d = adjust.Tweak(dbn, sat=1.7, cont=1.7)
dimming = fvf.rfs(dbn, dimming, mappings="[4193 4247] ")
dimming = fvf.rfs(dimming, dimming_a, mappings="31879")
dimming = fvf.rfs(dimming, dimming_b, mappings="31880")
dimming = fvf.rfs(dimming, dimming_c, mappings="31881")
dimming = fvf.rfs(dimming, dimming_d, mappings="[31882 31914]")

grain_1 = kgf.adaptive_grain(dimming, 0.4, luma_scaling=3)
grain_2 = kgf.adaptive_grain(dimming, 3, luma_scaling=3, static=False)
grain_3 = kgf.adaptive_grain(dimming, 1, luma_scaling=3, static=False)
grain = fvf.rfs(grain_1, grain_2, mappings="[274 344] [583 674]")
grain = fvf.rfs(grain, grain_3, mappings="[4319 4375] [31885 31914] [46340 46590] [52858 52984] [57066 57161]")

blank = core.std.BlankClip(src, length=2)
blank = kgf.insert_clip(grain, blank, 31913)

# OP filtering
op = scaled[opstart:opstart+2157]

op_temp = fvf.Depth(op, 8)
opY, U, V = kgf.split(op_temp)
op_mask = core.std.Expr(opY, expr=["x 235 > 250 0 ?"])
op_mask = kgf.iterate(op_mask, core.std.Maximum, 8)
op_mask = kgf.iterate(op_mask, core.std.Inflate, 10)
op_mask = fvf.Depth(op_mask, 16)

op_warp = core.warp.AWarpSharp2(op, thresh=96, chroma=1)
op_warp = fvf.rfs(op, op_warp, mappings="[286 428]")
op_warp = core.std.MaskedMerge(op_warp, op, op_mask)

op_aa = taa.TAAmbk(op_warp, aatype='Eedi3', opencl=True, cycle=1)
op_aa = fvf.rfs(op_warp, op_aa, mappings="[1242 1247] [1684 1686]")

op_dimming = adjust.Tweak(op_aa, sat=2, cont=2, bright=1.2)
op_dimming = fvf.rfs(op_aa, op_dimming, mappings="[1299 1332] [1361 1369]")

op_dblk = fvf.AutoDeblock(op_dimming)
op_dblk = fvf.rfs(op_dimming, op_dblk, mappings="[1299 1332] [1366 1369")

op_dbn_1 = core.f3kdb.Deband(op_dblk, range=17, y=48, cb=40, cr=40, grainy=12, grainc=0, output_depth=16)
op_dbn_2 = core.f3kdb.Deband(op_dblk, range=21, y=56, cb=48, cr=48, grainy=24, grainc=0, output_depth=16)
op_dbn = fvf.rfs(op_dbn_1, op_dbn_2, mappings="[0 146] [286 428] [702 915] [1020 1117] [1225 1274] [1299 1332] [1393 1427] [1368 1369]")
op_dbn = fvf.rfs(op_dbn, op, mappings="[147 215] [2132 2156]")

op_masked = core.std.MaskedMerge(op_dbn, op, op_mask)
op_masked = fvf.rfs(op_dbn, op_masked, mappings="[286 428]")

op_grain_1 = kgf.adaptive_grain(op_masked, 0.4, luma_scaling=3)
op_grain_2 = kgf.adaptive_grain(op_masked, 1, luma_scaling=3, static=False)
op_grain_3 = kgf.adaptive_grain(op_masked, 1, luma_scaling=3)
op_grain = fvf.rfs(op_grain_1, op_grain_2, mappings="[0 79] [286 428] [1225 1255] [1299 1332]")
op_grain = fvf.rfs(op_grain, op_grain_3, mappings="[80 146] [941 984] [1299 1427] [1500 1856] [2036 2131]")

final = kgf.insert_clip(blank, op_grain, opstart)

out = final
final = fvf.Depth(out, 10)
final.set_output()