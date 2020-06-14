import kagefunc as kgf
import lvsfunc as lvf
import vsTAAmbk as taa
from vsutil import depth

import vapoursynth as vs

core = vs.core
core.max_cache_size = 1024 * 8

opstart = 563
edstart = 32339

src_a = lvf.src(r"10/Kaguya_10_EN_HD.mp4")
src_b = lvf.src(r"10/[HorribleSubs] Kaguya-sama wa Kokurasetai - 10 [1080p].mkv")[13:]
blank = core.std.BlankClip(src_b)
src_b = src_b[:12046]+blank[0:2]+src_b[12062:]
scomp = lvf.comparison.stack_compare(src_a, src_b, height=480)

hardsubmask = kgf.hardsubmask(src_a, src_b)
src = core.std.MaskedMerge(src_a, src_b, hardsubmask)

src_fade = depth(kgf.hardsubmask_fades(src_a, src_b, highpass=1300), 8)
src_fade = core.std.MaskedMerge(src_a, src_b, src_fade)
src = lvf.rfs(src, src_fade, ranges = [({opstart, opstart + 2160}), (2841, 2924), (4739, 4751), (6379, 6390), (11841, 11971),
                                       (12149, 12255), (22234, 22245), (22278, 22289), (22901, 23006), (24830, 24845), (25587, 25603),
                                       (25621, 25649)])

scomp2 = lvf.comparison.stack_compare(src, src_a, height=480) # checking for leftover hardsubbed signs

scaled = kgf.inverse_scale(src, width=None, height=874, kernel='bicubic', b=0, c=1/2, mask_detail=True,
                           descale_mask_zones=[[0,opstart],[opstart,opstart + 2159],[edstart,edstart + 2157]])
scaled = core.resize.Spline36(scaled, 1280, 720, format=vs.YUV444P16)



# # # OP filtering # # #
op = scaled[opstart:opstart + 2157]

op_denoise = lvf.denoise.quick_denoise(op, h=0.7)

op_aa = taa.TAAmbk(op_denoise, aatype='Eedi3')

op_dbn_1 = core.f3kdb.Deband(op_aa, range=17, y=40, cb=32, cr=32, grainy=0, grainc=0, output_depth=16)
op_dbn_2 = core.f3kdb.Deband(op_aa, range=23, y=64, cb=56, cr=56, grainy=24, grainc=0, output_depth=16)
op_dbn = lvf.rfs(op_dbn_1, op_dbn_2, ranges = [(1110, 1197), (1519, 1589), (1686, 1770), (1857, 1989)])

# # # OP filtering # # #
# # # ED filtering # # #
ed = scaled[edstart:edstart + 2160]

ed_denoise = lvf.denoise.quick_denoise(ed, h=0.7)

ed_dbn_1 = core.f3kdb.Deband(ed_denoise, range=17, y=40, cb=32, cr=32, grainy=0, grainc=0, output_depth=16)
ed_dbn_2 = core.f3kdb.Deband(ed_denoise, range=23, y=64, cb=56, cr=56, grainy=24, grainc=0, output_depth=16)
ed_dbn = lvf.rfs(ed_dbn_1, ed_dbn_2, ranges = [(0, 174)])

# # # ED filtering # # #


denoise = lvf.denoise.quick_denoise(scaled, h=0.7)

aa_1 = taa.TAAmbk(denoise, aatype='Eedi3')
aa_2 = taa.TAAmbk(denoise, aatype=4)
aa = lvf.rfs(aa_1, aa_2, ranges = [])
aa = lvf.rfs(aa, denoise, ranges = [])

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

grainmask = core.std.Expr([
    core.adg.Mask(out, luma_scaling=2),
    core.adg.Mask(out, luma_scaling=12)
    ], expr="x y +")
grain = core.std.MaskedMerge(out, core.grain.Add(out, 1), grainmask)

final = depth(grain, 10)
final.set_output()
