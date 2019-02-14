import vapoursynth as vs
import adjust
import lvsfunc as lvf
import fvsfunc as fvf
import vsTAAmbk as taa
import kagefunc as kgf
core = vs.core
core.max_cache_size = 8192

opstart = 1200
edstart = 31770

src = lvf.src(r"06/The Rising of the Shield Hero E06 [1080p][AAC][JapDub][GerEngSub][Web-DL].mkv")
src = fvf.Depth(src, 16)


# # # # OP filtering # # # #

op = src[opstart:opstart+2157]

op_aa = taa.TAAmbk(op, aatype='Eedi3', opencl=True, cycle=1)
op_aa = fvf.rfs(op, op_aa, mappings="[1242 1247] [1684 1686]")

op_dimming = adjust.Tweak(op_aa, sat=2, cont=2, bright=1.2)
op_dimming = fvf.rfs(op_aa, op_dimming, mappings="[1299 1332] [1361 1369]")

op_credit_mask = core.resize.Spline36(core.imwri.Read(r"02/ShieldbroOP_mask.png"), format=vs.GRAY16, matrix_s='709')
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
aa = fvf.rfs(aa_1, aa_2, mappings="")

dbn = core.f3kdb.Deband(aa, range=21, y=56, cb=48, cr=48, grainy=24, grainc=0, output_depth=16)
dbn = fvf.rfs(dbn, aa, mappings="[7020 7090] [12341 12379] [12569 12604]")

# fuck dimming tbh
dim1 = adjust.Tweak(dbn, sat=1.1, cont=1.1, bright=0)
dim2 = adjust.Tweak(dbn, sat=1.15, cont=1.15, bright=0)
dim3 = adjust.Tweak(dbn, sat=1.3, cont=1.3, bright=0)
dim4 = adjust.Tweak(dbn, sat=1.4, cont=1.4, bright=0)
dim5 = adjust.Tweak(dbn, sat=1.5, cont=1.5, bright=0)
dimming = fvf.rfs(dbn, dim1, mappings="15403 [15441 15446] ")
dimming = kgf.insert_clip(dimming, dimming[15403], 15404)
dimming = fvf.rfs(dimming, dim2, mappings="28383 28384")
dimming = fvf.rfs(dimming, dim3, mappings="28382 [28423 28449]")
dimming = fvf.rfs(dimming, dim4, mappings="[15405 15440] [15447 15459] [28377 28381]")
dimming = fvf.rfs(dimming, dim5, mappings="[28294 28335] ")

grain = kgf.adaptive_grain(dimming, 0.4, luma_scaling=3)


final = kgf.insert_clip(grain, op_grain, opstart)
final = kgf.insert_clip(final, ed_grain, edstart)

out = final
final = fvf.Depth(out, 10)
final.set_output()
