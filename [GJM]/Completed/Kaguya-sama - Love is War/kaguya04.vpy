import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import vsTAAmbk as taa
core = vs.core
core.max_cache_size = 8192

opstart = 1366
edstart = 32363

src_a = lvf.src(r"04/Kaguya_04_FR_HD.mp4")
src_b = lvf.src(r"04/[HorribleSubs] Kaguya-sama wa Kokurasetai - 04 [1080p].mkv")
src_b = src_b[2:18867]+src_b[18869:]
hardsubmask = kgf.hardsubmask(src_a, src_b)
src = core.std.MaskedMerge(src_a, src_b, hardsubmask)

src_fade = fvf.Depth(kgf.hardsubmask_fades(src_a, src_b, highpass=1300), 8)
src_fade = core.std.MaskedMerge(src_a, src_b, src_fade)					# NOTE: FRAMERANGES FOR UP TO '6700' ARE INTRO. DON'T REMOVE THEM UNLESS INTRO CHANGES.
src = fvf.ReplaceFramesSimple(src, src_fade, mappings=f"[{opstart} {opstart+2500}] [3306 3326] [3361 3374] [4018 4089] [5978 5995] 8698 [9291 9404] [19477 19589] [23851 23868] [24969 25080] [15913 15957]")
src = kgf.insert_clip(src, src[18867], 18865)
src = kgf.insert_clip(src, src[18867], 18866)
src = kgf.insert_clip(src, src_a[30231:30321], 30231)
src = src[:34522]

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
aa = fvf.rfs(aa_1, aa_2, mappings=f"[7852 7918]")
aa = fvf.rfs(aa, denoise, mappings=f"[30231 30320]")

dbn_1 = core.f3kdb.Deband(aa, range=17, y=40, cb=32, cr=32, grainy=0, grainc=0, output_depth=16)
dbn_2 = core.f3kdb.Deband(aa, range=20, y=40, cb=32, cr=32, grainy=0, grainc=0, output_depth=16)
dbn_3 = core.f3kdb.Deband(aa, range=23, y=64, cb=56, cr=56, grainy=24, grainc=0, output_depth=16)
dbn = fvf.rfs(dbn_1, dbn_2, mappings=f"")
dbn = fvf.rfs(dbn, dbn_3, mappings=f"[580 786] [1149 1178] [4214 4388] [4431 4772] [5129 5218] [5765 5929] [6311 6445] [6742 6879] [7123 7329] [7984 8099] [8199 8639] [9090 9173] [9703 10055] [10339 10368] [10828 10890] [11415 11597] [11700 11985] [12064 12312] [12565 [12700 13431] [13708 13785] [13828 13983] [14224 14912] [14997 15668] [15714 16118] [16254 16775] [16962 17069] [17166 17321] [17580 17813] [17856 18056] [18201 18608] [18819 18864] [19006 19317] [19453 19692] [20005 20160] [20455 20478] [20626 20763] [21417 21733] [22439 22606] [23269 23442] [23587 23778] [23827 23910] [24037 24192] [25204 25403] [25713 25808] [25854 25913] [26130 26561] [26728 26823] [27229 27297] [27418 28673] [28740 28865] [28894 29189] [29298 29507] [29556 30230] [30381 30734] [31649 31688]")


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

final = fvf.Depth(grain, 10)
final.set_output()