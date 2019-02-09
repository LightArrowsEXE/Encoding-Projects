import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import vsTAAmbk as taa
core = vs.core
core.max_cache_size = 8192

opstart = 1318
edstart = 32367

src_a = lvf.src(r"..\02\Kaguya-sama Love is War E02 [1080p][AAC][JapDub][GerSub][Web-DL].mp4")
src_b = lvf.src(r"..\02\[HorribleSubs] Kaguya-sama wa Kokurasetai - 02 [1080p].mkv")
hardsubmask = kgf.hardsubmask(src_a, src_b)
src = core.std.MaskedMerge(src_a, src_b, hardsubmask)

src_fade = fvf.Depth(kgf.hardsubmask_fades(src_a, src_b, highpass=1300), 8)
src_fade = core.std.MaskedMerge(src_a, src_b, src_fade)					# NOTE: FRAMERANGES FOR UP TO '6700' ARE INTRO. DON'T REMOVE THEM UNLESS INTRO CHANGES.
src = fvf.ReplaceFramesSimple(src, src_fade, mappings=f"[{opstart+300} {opstart+500}] [0 80][1100 {opstart}][{opstart+2150} 3650][6000 6700] [11169 11189] [11358 11364] [13235 13243] [13283 13286] [13580 13685] [13841 13844] [15307 15346] [15663 15704] [17956 17977] [21832 21841] [21891 21895] [21924 21927] [22058 22128] [22312 22417] [22823 22825] [23720 23739] [24924 24986] [25447 25543] [26539 26786] [28727 28806] [32325 {edstart}]")

scaled = kgf.inverse_scale(src, width=None, height=874, kernel='bicubic', a1=0, a2=1/2, mask_detail=True, masking_areas=[[1209,opstart],[opstart,opstart+2159],[edstart,edstart+2157]])
scaled = core.resize.Spline36(scaled, 1280, 720, format=vs.YUV444P16)

# # # OP filtering # # #
op = scaled[opstart:opstart+2157]

op_denoise = lvf.denoise(op, h=0.7)

op_aa = taa.TAAmbk(op_denoise, aatype='Eedi3')

op_dbn_1 = core.f3kdb.Deband(op_aa, range=17, y=40, cb=32, cr=32, grainy=0, grainc=0, output_depth=16)
op_dbn_2 = core.f3kdb.Deband(op_aa, range=23, y=64, cb=56, cr=56, grainy=24, grainc=0, output_depth=16)
op_dbn = fvf.rfs(op_dbn_1, op_dbn_2, mappings="[1110 1197][1519 1589][1686 1770][1857 1989]")

op_grain = kgf.adaptive_grain(op_dbn, 0.5, luma_scaling=12)

# # # OP filtering # # #
# # # ED filtering # # #
ed = scaled[edstart:edstart+2160]

ed_denoise = lvf.denoise(ed, h=0.7)

ed_dbn_1 = core.f3kdb.Deband(ed_denoise, range=17, y=40, cb=32, cr=32, grainy=0, grainc=0, output_depth=16)
ed_dbn_2 = core.f3kdb.Deband(ed_denoise, range=23, y=64, cb=56, cr=56, grainy=24, grainc=0, output_depth=16)
ed_dbn = fvf.rfs(ed_dbn_1, ed_dbn_2, mappings="[1555 1571] [1851 1885]")

ed_grain = kgf.adaptive_grain(ed_dbn, 0.5, luma_scaling=12)

# # # ED filtering # # #

denoise = lvf.denoise(scaled, h=0.7)
aa = taa.TAAmbk(denoise, aatype='Eedi3')

dbn_1 = core.f3kdb.Deband(aa, range=17, y=40, cb=32, cr=32, grainy=0, grainc=0, output_depth=16)
dbn_2 = core.f3kdb.Deband(aa, range=20, y=40, cb=32, cr=32, grainy=0, grainc=0, output_depth=16)
dbn_3 = core.f3kdb.Deband(aa, range=23, y=64, cb=56, cr=56, grainy=24, grainc=0, output_depth=16)
dbn = fvf.rfs(dbn_1, dbn_2, mappings="[300 491]")
dbn = fvf.rfs(dbn, dbn_3, mappings="[5380 5534] [5710 6154] [9703 9720] [9987 10032] [18362 18546] [19487 19525] [20678 20691] [24092 24177] [28487 28591] [29951 30261] [30449 30491] [30623 31003] [31004 31514]")

grain_1 = kgf.adaptive_grain(dbn, 0, luma_scaling=2, show_mask=True)
grain_2 = kgf.adaptive_grain(dbn, 0, luma_scaling=12, show_mask=True)
grainmask = core.std.Expr([grain_1, grain_2], expr="x y +")
grain = core.std.MaskedMerge(dbn, core.grain.Add(dbn, 1), grainmask)

op_out = op_grain
ed_out = ed_grain
grain = dbn
out = grain

insert = kgf.insert_clip(out, op_out, opstart)
insert = kgf.insert_clip(insert, ed_out[1:2159], edstart) # I don't get why this doesn't work without cutting part of it??

final = fvf.Depth(insert, 10)
final.set_output()