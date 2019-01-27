import vapoursynth as vs
import adjust
import lvsfunc as lvf
import fvsfunc as fvf
import vsTAAmbk as taa
import kagefunc as kgf
core = vs.core
core.max_cache_size = 8192

opstart = 1224
edstart = 31768

src = lvf.src(r"The Rising of the Shield Hero E03 [1080p][AAC][JapDub][GerEngSub][Web-DL].mkv")
src = fvf.Depth(src, 16)


# # # # OP filtering # # # #
op = src[opstart:opstart+2157]

op_aa = taa.TAAmbk(op, aatype='Eedi3', opencl=True, cycle=1)
op_aa = fvf.rfs(op, op_aa, mappings="[1242 1247] [1684 1686]")

op_dimming = adjust.Tweak(op_aa, sat=2, cont=2, bright=1.2)
op_dimming = fvf.rfs(op_aa, op_dimming, mappings="[1299 1332] [1361 1369]")

op_credit_mask = core.resize.Spline36(core.imwri.Read(r"ShieldbroOP_mask.png"), format=vs.GRAY16, matrix_s='709')
op_credit_mask = kgf.iterate(op_credit_mask, core.std.Deflate, 5)
op_credit_mask = kgf.iterate(op_credit_mask, core.std.BoxBlur, 2)
op_credit = core.std.MaskedMerge(op_dimming, op_aa, op_credit_mask)

op_dblk = fvf.AutoDeblock(op_credit)
op_dblk = fvf.rfs(op_credit, op_dblk, mappings="[1299 1332] [1366 1369]")

op_dbn_1 = core.f3kdb.Deband(op_dblk, range=17, y=48, cb=40, cr=40, grainy=12, grainc=0, output_depth=16)
op_dbn_2 = core.f3kdb.Deband(op_dblk, range=21, y=56, cb=48, cr=48, grainy=24, grainc=0, output_depth=16)
op_dbn = fvf.rfs(op_dbn_1, op_dbn_2, mappings="[0 146] [286 428] [702 915] [1020 1117] [1225 1274] [1299 1332] [1393 1427] [1368 1369]")
op_dbn = fvf.rfs(op_dbn, op, mappings="[147 215] [2132 2156]")

op_grain_1 = kgf.adaptive_grain(op_dbn, 0.4, luma_scaling=3)
op_grain_2 = kgf.adaptive_grain(op_dbn, 3, luma_scaling=3, static=False)
op_grain_3 = kgf.adaptive_grain(op_dbn, 1, luma_scaling=3)
op_grain = fvf.rfs(op_grain_1, op_grain_2, mappings="[0 79]")
op_grain = fvf.rfs(op_grain, op_grain_3, mappings="[80 146] [286 428] [941 984] [1299 1427] [1500 1856] [2036 2131] [1225 1255] [1299 1332]")
# # # # OP filtering # # # #
# # # # ED filtering (lol what filtering) # # # #
ed = src[edstart:edstart+2157]

ed_grain = kgf.adaptive_grain(ed, 0.3)

# # # # ED filtering (lol what filtering) # # # #


aa_1 = taa.TAAmbk(src, aatype='Eedi3', opencl=True)
aa_2 = taa.TAAmbk(src, aatype='Eedi3', opencl=True, cycle=3)
aa_3 = taa.TAAmbk(src, aatype=4, cycle=1)
aa = fvf.rfs(aa_1, aa_2, mappings="0")
aa = fvf.rfs(aa, aa_3, mappings="[5438 5514]")

dbn = core.f3kdb.Deband(aa, range=21, y=56, cb=48, cr=48, grainy=24, grainc=0, output_depth=16)
dbn = fvf.rfs(dbn, aa, mappings="[6237 6325] [9151 9216] [12027 12080] [12129 12199] [15943 16084] [16231 16287] [16383 16471] [16823 16957] [20172 20266] [28505 28623]")

dimming_1 = adjust.Tweak(dbn, sat=1.7, cont=1.7, bright=0)
dimming_2 = adjust.Tweak(dbn, sat=2, cont=2, bright=0)
dimming_3 = adjust.Tweak(dbn, sat=3, cont=3, bright=0)
dimming = fvf.rfs(dbn, dimming_1, mappings="[20704 20724] ")
dimming = fvf.rfs(dimming, dimming_2, mappings="[22287 22292] [27110 27122] ")
dimming = fvf.rfs(dimming, dimming_2, mappings="[27024 27043] [27053 27054] 27123")
dim1 = adjust.Tweak(dbn, sat=1.05, cont=1.05, bright=0)
dim2 = adjust.Tweak(dbn, sat=1.1, cont=1.1, bright=0)
dim3 = adjust.Tweak(dbn, sat=1.15, cont=1.15, bright=0)
dim4 = adjust.Tweak(dbn, sat=1.2, cont=1.2, bright=0)
dim5 = adjust.Tweak(dbn, sat=1.25, cont=1.25, bright=0)
dim6 = adjust.Tweak(dbn, sat=1.3, cont=1.3, bright=0)
dim7 = adjust.Tweak(dbn, sat=1.38, cont=1.38, bright=0)
dim8 = adjust.Tweak(dbn, sat=1.45, cont=1.45, bright=0)
dim9 = adjust.Tweak(dbn, sat=1.55, cont=1.55, bright=0)
dim10 = adjust.Tweak(dbn, sat=1.6, cont=1.6, bright=0)
dimming = fvf.rfs(dimming, dim1, mappings="20695")
dimming = fvf.rfs(dimming, dim2, mappings="20696 27264")
dimming = fvf.rfs(dimming, dim3, mappings="20697 [27180 27194]")
dimming = fvf.rfs(dimming, dim4, mappings="20698 27045 27265")
dimming = fvf.rfs(dimming, dim5, mappings="20699")
dimming = fvf.rfs(dimming, dim6, mappings="20700 23388 [24252 24256] [27088 27109] 27195 27196 27199 [27201 27207] 27266")
dimming = fvf.rfs(dimming, dim7, mappings="20701")
dimming = fvf.rfs(dimming, dim8, mappings="20702 27267")
dimming = fvf.rfs(dimming, dim9, mappings="20703 27044 27197 27198 27200 27268 27269")

dim = dimming[27195]+dimming[27199]

grain_1 = kgf.adaptive_grain(dimming, 0.4, luma_scaling=3)
grain_2 = kgf.adaptive_grain(dimming, 3, luma_scaling=3, static=False)
grain_3 = kgf.adaptive_grain(dimming, 1, luma_scaling=3)
grain = fvf.rfs(grain_1, grain_2, mappings="0")
grain = fvf.rfs(grain, grain_3, mappings="[27053 27054]")

final = kgf.insert_clip(grain, op_grain, opstart)
final = kgf.insert_clip(final, ed_grain, edstart)

#temp = lvf.src(r"Tate03 (premux) (1).mkv")


out = final
final = fvf.Depth(out, 10)
fix = final[:3381]
#comp = lvf.stack_compare(temp, fix, height=480)
fix.set_output()
