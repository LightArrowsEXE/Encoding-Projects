import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import vsTAAmbk as taa
core = vs.core
core.max_cache_size = 8192

opstart = 670
edstart = 32173

src_a = lvf.src(r"Kaguya_03_DE_HD.mp4")
src_b = lvf.src(r"[HorribleSubs] Kaguya-sama wa Kokurasetai - 03 [1080p].mkv")
src_b = src_b[2:]
hardsubmask = kgf.hardsubmask(src_a, src_b)
src = core.std.MaskedMerge(src_a, src_b, hardsubmask)

src_fade = fvf.Depth(kgf.hardsubmask_fades(src_a, src_b, highpass=1300), 8)
src_fade = core.std.MaskedMerge(src_a, src_b, src_fade)					# NOTE: FRAMERANGES FOR UP TO '6700' ARE INTRO. DON'T REMOVE THEM UNLESS INTRO CHANGES.
src = fvf.ReplaceFramesSimple(src, src_fade, mappings=f"[0 {opstart+2500}] [3306 3326] [3361 3374] [4018 4089] [5978 5995] [7422 7453] [7464 7511] [8200 8204] [8398 8511] [12873 12889] [12903 12912] [12941 12951] [13696 13806] [15614 15829] [16581 16586] [16613 16625] [17093 17107] [17125 17137] [17156 17166] [17181 17189] [17217 17225] [17240 17248] [19825 19916] [22088 22097] [22119 22214] [22436 22446] [22455 22465] [22491 22500] [22848 22931] [25035 25263]")
src = src[:34523]

scaled = kgf.inverse_scale(src, width=None, height=874, kernel='bicubic', a1=0, a2=1/2, mask_detail=True, masking_areas=[[0,opstart],[opstart,opstart+2159],[edstart,edstart+2157]])
scaled = core.resize.Spline36(scaled, 1280, 720, format=vs.YUV444P16)

# # # OP filtering # # #
op = scaled[opstart:opstart+2157]

op_denoise = lvf.denoise(op, h=0.7)

op_aa = taa.TAAmbk(op_denoise, aatype='Eedi3')

op_dbn_1 = core.f3kdb.Deband(op_aa, range=17, y=40, cb=32, cr=32, grainy=0, grainc=0, output_depth=16)
op_dbn_2 = core.f3kdb.Deband(op_aa, range=23, y=64, cb=56, cr=56, grainy=24, grainc=0, output_depth=16)
op_dbn = fvf.rfs(op_dbn_1, op_dbn_2, mappings="[1110 1197][1519 1589][1686 1770][1857 1989]")


# # # OP filtering # # #
# # # ED filtering # # #
ed = scaled[edstart:edstart+2160]

ed_denoise = lvf.denoise(ed, h=0.7)

ed_dbn_1 = core.f3kdb.Deband(ed_denoise, range=17, y=40, cb=32, cr=32, grainy=0, grainc=0, output_depth=16)
ed_dbn_2 = core.f3kdb.Deband(ed_denoise, range=23, y=64, cb=56, cr=56, grainy=24, grainc=0, output_depth=16)
ed_dbn = fvf.rfs(ed_dbn_1, ed_dbn_2, mappings="[0 174]")

# # # ED filtering # # #

denoise = lvf.denoise(scaled, h=0.7)
aa_1 = taa.TAAmbk(denoise, aatype='Eedi3')
aa_2 = taa.TAAmbk(denoise, aatype=4)
aa = fvf.rfs(aa_1, aa_2, mappings=f"[8512 9069]")

dbn_1 = core.f3kdb.Deband(aa, range=17, y=40, cb=32, cr=32, grainy=0, grainc=0, output_depth=16)
dbn_2 = core.f3kdb.Deband(aa, range=20, y=40, cb=32, cr=32, grainy=0, grainc=0, output_depth=16)
dbn_3 = core.f3kdb.Deband(aa, range=23, y=64, cb=56, cr=56, grainy=24, grainc=0, output_depth=16)
dbn = fvf.rfs(dbn_1, dbn_2, mappings=f"0")
dbn = fvf.rfs(dbn, dbn_3, mappings=f"[430 {opstart}] [3256 3264] [6152 6507] [8370 8397] [8512 9105] [9837 9932] [10518 10546] [11015 11086] [11702 11797] [11993 12409] [13808 13908] [13948 14055] [15006 15059] [15315 15457] [17488 17544] [17988 18107] [18204 18266] [18756 18980] [19014 19052] [19497 19568] [20233 20316] [20886 20939] [21354 21557] [21858 21890] [21927 21980] [22359 22490] [22848 22931] [22986 23057] [23175 23312] [24192 24260] [24321 24428] [25330 25371] [25597 25695] [25945 26040] [27724 27777] [30397 30420] [30874 30963] [31252 31281] [31294 31464] [31537 31608] [32053 32172]")


op_out = op_dbn
ed_out = ed_dbn
grain = dbn
out = dbn

insert = kgf.insert_clip(out, op_out, opstart)
insert = kgf.insert_clip(insert, ed_out[1:2160], edstart) # I don't get why this doesn't work without cutting part of it??

grain_1 = kgf.adaptive_grain(out, 0, luma_scaling=2, show_mask=True)
grain_2 = kgf.adaptive_grain(out, 0, luma_scaling=12, show_mask=True)
grainmask = core.std.Expr([grain_1, grain_2], expr="x y +")
grain = core.std.MaskedMerge(out, core.grain.Add(out, 1), grainmask)

final = fvf.Depth(grain, 10) #sakuga: 7179, 15315, 17545
ED = final[edstart:]
ED = core.std.CropRel(ED, 0, 0, 89, 89)
ED.set_output()