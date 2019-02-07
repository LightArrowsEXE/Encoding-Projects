import vapoursynth as vs
import adjust
import lvsfunc as lvf
import fvsfunc as fvf
import vsTAAmbk as taa
import kagefunc as kgf
core = vs.core
core.max_cache_size = 8192

opstart = 2997
edstart = 30928

src = lvf.src(r"The Rising of the Shield Hero E02 [1080p][AAC][JapDub][GerEngSub][Web-DL].mkv")
src = fvf.Depth(src, 16)

scaled = core.std.CropRel(src, 2, 2, 0, 0)
scaled = core.resize.Spline36(scaled, 1920, 1080)

# # # # OP filtering # # # #
op = scaled[opstart:opstart+2157]

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
op_grain_2 = kgf.adaptive_grain(op_dbn, 2, luma_scaling=3, static=False)
op_grain_3 = kgf.adaptive_grain(op_dbn, 1, luma_scaling=3)
op_grain = fvf.rfs(op_grain_1, op_grain_2, mappings="[0 79]")
op_grain = fvf.rfs(op_grain, op_grain_3, mappings="[80 146] [286 428] [941 984] [1299 1427] [1500 1856] [2036 2131] [1225 1255] [1299 1332]")
# # # # OP filtering # # # #
# # # # ED filtering (lol what filtering) # # # #
ed = scaled[edstart:edstart+2157]

ed_grain = kgf.adaptive_grain(ed, 0.3)

# # # # ED filtering (lol what filtering) # # # #


aa_1 = taa.TAAmbk(scaled, aatype='Eedi3', opencl=True)
aa_2 = taa.TAAmbk(scaled, aatype='Eedi3', opencl=True, cycle=3)

dbn_1 = core.f3kdb.Deband(aa_1, range=21, y=56, cb=48, cr=48, grainy=24, grainc=0, output_depth=16)
dbn_2 = core.f3kdb.Deband(aa_2, range=21, y=56, cb=48, cr=48, grainy=24, grainc=0, output_depth=16)
dbn_3 = core.f3kdb.Deband(aa_1, range=21, y=56, cb=48, cr=48, grainy=24, grainc=0, output_depth=16)
dbn = fvf.rfs(dbn_1, dbn_2, mappings="0")
dbn = fvf.rfs(dbn, dbn_3, mappings="[29176 29178]")
dbn = fvf.rfs(dbn, aa_1, mappings="[7311 7360] [7472 7569] [10543 10759] [12892 12957] [13660 14491] [14597 14739] [14790 14890] [15341 15406] [15603 16287] [16723 17049] [17133 17317] [18006 18040] [18204 18247] [19711 19779] [20979 21035] [22402 22520] [22913 23014] [23377 23436] [23479 23537] [23982 24051] [24894 24970] [25132 25183] [25426 25488] [25500 25506] [25766 25920] [26131 26208] [26297 26383] [27834 27858] [27895 27924] [27984 28030] [28469 28547] [29113 29162] [29408 29425] [29455 29489] [30305 ")
dbn = fvf.rfs(dbn, aa_2, mappings="0")

dimming = adjust.Tweak(dbn, sat=4, cont=3.5, bright=2)
dimming = fvf.rfs(dbn, dimming, mappings="[29176 29186]")
dbn = dimming

grain_1 = kgf.adaptive_grain(dbn, 0.4, luma_scaling=3)
grain_2 = kgf.adaptive_grain(dbn, 3, luma_scaling=3, static=False)
grain_3 = kgf.adaptive_grain(dbn, 1, luma_scaling=3)
grain = fvf.rfs(grain_1, grain_2, mappings="[15603 16287] [29176 29178]")
grain = fvf.rfs(grain, grain_3, mappings="0")

final = kgf.insert_clip(grain, op_grain, opstart)
final = kgf.insert_clip(final, ed_grain, edstart)

out = final
final = fvf.Depth(out, 10)
OP = final[opstart:opstart+2157]
ED = final[edstart:edstart+2157]
final.set_output()
