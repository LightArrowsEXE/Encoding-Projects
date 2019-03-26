import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import vsTAAmbk as taa
core = vs.core
core.max_cache_size = 8192

opstart = 1196
edstart = 28096

src_a = lvf.src(r"11/Kaguya_11_EN_HD.mp4")[:34522]
src_b = lvf.src(r"11/[HorribleSubs] Kaguya-sama wa Kokurasetai - 11 [1080p].mkv")[4:]
blank = core.std.BlankClip(src_b)
#src_b = src_b[:12046]+blank[0:2]+src_b[12062:]
scomp = lvf.stack_compare(src_a, src_b, height=480)

hardsubmask = kgf.hardsubmask(src_a, src_b)
src = core.std.MaskedMerge(src_a, src_b, hardsubmask)

src_fade = fvf.Depth(kgf.hardsubmask_fades(src_a, src_b, highpass=1300), 8)
src_fade = core.std.MaskedMerge(src_a, src_b, src_fade)
src = fvf.ReplaceFramesSimple(src, src_fade, mappings=f"[{opstart} {opstart+2160}] [3509 3628] [12864 12889] [13103 13215] [15182 15194] [22134 22254] [27904 28045] [34405 34521]")

scomp2 = lvf.stack_compare(src, src_a, height=480) # checking for leftover hardsubbed signs

scaled = kgf.inverse_scale(src, width=None, height=874, kernel='bicubic', a1=0, a2=1/2, mask_detail=True, masking_areas=[[0,opstart],[opstart,opstart+2159],[edstart,edstart+2157]])
scaled = core.resize.Spline36(scaled, 1280, 720, format=vs.YUV444P16)



# # # OP filtering # # #
op = scaled[opstart:opstart+2157]

op_denoise = lvf.quick_denoise(op, h=0.7)

op_aa = taa.TAAmbk(op_denoise, aatype='Eedi3')

op_dbn_1 = core.f3kdb.Deband(op_aa, range=17, y=40, cb=32, cr=32, grainy=0, grainc=0, output_depth=16)
op_dbn_2 = core.f3kdb.Deband(op_aa, range=23, y=64, cb=56, cr=56, grainy=24, grainc=0, output_depth=16)
op_dbn = fvf.rfs(op_dbn_1, op_dbn_2, mappings="[1110 1197][1519 1589][1686 1770][1857 1989]")

# # # OP filtering # # #
# # # ED filtering # # #
ed = scaled[edstart:edstart+2160]

ed_denoise = lvf.quick_denoise(ed, h=0.7)

ed_dbn_1 = core.f3kdb.Deband(ed_denoise, range=17, y=40, cb=32, cr=32, grainy=0, grainc=0, output_depth=16)
ed_dbn_2 = core.f3kdb.Deband(ed_denoise, range=23, y=64, cb=56, cr=56, grainy=24, grainc=0, output_depth=16)
ed_dbn = fvf.rfs(ed_dbn_1, ed_dbn_2, mappings="[0 174]")

# # # ED filtering # # #


denoise = lvf.quick_denoise(scaled, h=0.7)

aa_1 = taa.TAAmbk(denoise, aatype='Eedi3')
aa_2 = taa.TAAmbk(denoise, aatype=4)
aa = fvf.rfs(aa_1, aa_2, mappings="")
aa = fvf.rfs(aa, denoise, mappings="")

dbn_1 = core.f3kdb.Deband(aa, range=17, y=40, cb=32, cr=32, grainy=0, grainc=0, output_depth=16)
dbn_2 = core.f3kdb.Deband(aa, range=23, y=64, cb=56, cr=56, grainy=24, grainc=0, output_depth=16)
dbn_mask = kgf.adaptive_grain(scaled, show_mask=True)
dbn = core.std.MaskedMerge(dbn_1, dbn_2, dbn_mask)
# Decided to just lazy it. I can care about everything looking perfect with BDs

op_out = op_dbn
ed_out = ed_dbn
out = dbn

insert = kgf.insert_clip(out, op_out, opstart)
insert = kgf.insert_clip(insert, ed_out[1:2160], edstart) # I don't get why this doesn't work without cutting part of it??

grain_1 = kgf.adaptive_grain(out, 0, luma_scaling=2, show_mask=True)
grain_2 = kgf.adaptive_grain(out, 0, luma_scaling=12, show_mask=True)
grainmask = core.std.Expr([grain_1, grain_2], expr="x y +")
grain = core.std.MaskedMerge(out, core.grain.Add(out, 1), grainmask)

final = fvf.Depth(grain, 10)
final.set_output()