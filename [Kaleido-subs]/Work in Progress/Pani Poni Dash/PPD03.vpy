import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import vsTAAmbk as taa
import havsfunc as haf
import finesharp
core = vs.core

opstart = 1463
edstart = 30834

src = lvf.src(r"[BDMV][Pani Poni Dash][ぱにぽにだっしゅ！][BD BOX]/DISC1/BDMV/STREAM/00005.m2ts")
NCOP = lvf.src(r"[BDMV][Pani Poni Dash][ぱにぽにだっしゅ！][BD BOX]/DISC6/BDMV/STREAM/00007.m2ts")
NCED = lvf.src(r"[BDMV][Pani Poni Dash][ぱにぽにだっしゅ！][BD BOX]/DISC6/BDMV/STREAM/00019.m2ts")
endcard = lvf.src(r"[BDMV][Pani Poni Dash][ぱにぽにだっしゅ！][BD BOX]/DISC6/BDMV/STREAM/00103.m2ts")

src = src[70802:105137]
src = core.std.CropRel(src, 20, 20, 8, 6)
src = fvf.Depth(src, 16)

scaled = core.resize.Spline36(src, 1280, 720, format=vs.YUV444P16)

def high_dehalo(clip):
	Y_filt = core.knlm.KNLMeansCL(clip, d=0, a=3, h=20)
	Y_filt = haf.FineDehalo(Y_filt, rx=2, ry=4, thmi=250, thma=255, thlimi=64, thlima=100, darkstr=0, brightstr=0, showmask=0, edgeproc=0)
	Y_merge = core.std.MaskedMerge(Y_filt, Y, kgf.retinex_edgemask(Y))
	return Y_merge

def low_dehalo(clip):
	Y_grain = core.knlm.KNLMeansCL(clip, d=0, a=3, h=2)
	Y_dehalo = haf.FineDehalo(Y_grain, rx=2, thmi=250, thma=255, thlimi=64, thlima=100)
	
	Y_mask = kgf.retinex_edgemask(clip)
	Y_mask = fvf.Depth(Y_mask, 8)
	Y_mask = kgf.iterate(Y_mask, core.std.Maximum, 3).std.Binarize()
	Y_mask = fvf.Depth(Y_mask, 16)
	Y_masked = core.std.MaskedMerge(Y_dehalo, clip, Y_mask)
	return Y_masked

# # # # OP FILTERING # # # #

NCOP = NCOP[24:2183]
NCOP = core.std.CropRel(NCOP, 20, 20, 8, 6)
NCOP = fvf.Depth(NCOP, 16)
NCOP = core.resize.Spline36(NCOP, 1280, 720, format=vs.YUV444P16)

OP = scaled[opstart:opstart+2158]

# Check these every episode
OP = NCOP[:13]+OP[13:241]+NCOP[243:278]+OP[276:1465]+NCOP[1467]+NCOP[1467:1564]+OP[1563:1608]+NCOP[1609:1642]+OP[1641:2005]+NCOP[2007:2159]+NCOP[2158]

Y, U, V = kgf.split(OP)

op_Ya = low_dehalo(Y)
op_Yb = high_dehalo(Y)
op_Y = fvf.rfs(op_Ya, op_Yb, mappings="[134 140] [146 242] [268 275] [408 541] [777 810] [1334 1541]")
op_Y = fvf.rfs(op_Y, Y, mappings="[543 611]")

op_Yqden = lvf.qden(op_Y, h=30, sigma=40)
op_Yqden = fvf.rfs(op_Y, op_Yqden, mappings="[1556 1596]")

op_Ysharp = haf.LSFmod(op_Yqden, strength=80, soft=10, edgemode=1, Smethod=2, Lmode=2)

op_merge = kgf.join([op_Ysharp, U, V])

op_aa_1 = taa.TAAmbk(op_merge, aatype='Eedi3')
op_aa_2 = taa.TAAmbk(op_merge, aatype='Nnedi3UpscaleSangNom')
op_aa = fvf.rfs(op_aa_1, op_aa_2, mappings="[0 67] [80 132] [146 242] [1315 1466] [1732 1875]")

op_deband = core.f3kdb.Deband(op_aa, range=17, y=40, cb=32, cr=32, grainy=12, grainc=0, output_depth=16)
op_grain = kgf.adaptive_grain(op_deband, 0.5)

op_out = op_grain

# # # # OP FILTERING # # # #
# # # # ED FILTERING # # # #

NCED = NCED[24:2182]
NCED = core.std.CropRel(NCED, 20, 20, 8, 6)
NCED = fvf.Depth(NCED, 16)
NCED = core.resize.Spline36(NCED, 1280, 720, format=vs.YUV444P16)

ED = scaled[edstart:edstart+2158]

# NCED looks a lot better overall, and unlike the OP the credits are just added on
ed_hmask = kgf.hardsubmask_fades(ED, NCED)
ed_hmasked = core.std.MaskedMerge(NCED, ED, ed_hmask)

ed_qden = lvf.qden(ed_hmasked, h=1.6, sigma=5)
ed_csharp = haf.LSFmod(ed_qden, strength=80, soft=10, edgemode=1, Smethod=2, Lmode=2)
ed_aa = taa.TAAmbk(ed_csharp, aatype='Eedi3')

ed_out = ed_aa

# # # # ED FILTERING # # # #

Y, U, V = kgf.split(scaled)

Y_a = low_dehalo(Y)
Y_b = high_dehalo(Y)
Y = fvf.rfs(Y_a, Y_b, mappings="[17484 17583]")

Y_sharp = haf.LSFmod(Y, strength=80, soft=10, edgemode=1, Smethod=2, Lmode=2)
merge = kgf.join([Y_sharp, U, V])

aa = taa.TAAmbk(merge, aatype='Eedi3')

deband_a = core.f3kdb.Deband(aa, range=17, y=40, cb=32, cr=32, grainy=12, grainc=0, output_depth=16)
grain = kgf.adaptive_grain(deband_a, 0.5)

out = kgf.insert_clip(grain, op_out, opstart)
out = kgf.insert_clip(out, ed_out, edstart)

endcard = core.std.CropRel(endcard, 160, 160, 96, 96)
endcard = core.resize.Spline36(core.std.AssumeFPS(endcard, fpsnum=24000, fpsden=1001), 1280, 720, format=vs.YUV444P16)
endcard = endcard[0]*72

out = out+endcard

# check if proper ED is used & if OP/ED are cut right
comp  = lvf.comp(scaled, out, [opstart+400, opstart+1000, opstart+1700, edstart+400, edstart+1000, edstart+1700])
scomp = lvf.scomp(scaled[opstart+2158]+scaled[edstart+2158], out[opstart+2158]+out[edstart+2158], height=480)

# Check random scenes in the episode
ep_comp = lvf.comp(scaled, out, [4351, 8058, 11355, 16032, 18048, 21842, 23435, 26274, 29340])

final = fvf.Depth(out, 10)
final.set_output()