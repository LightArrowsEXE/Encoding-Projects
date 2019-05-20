import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import vsTAAmbk as taa
import havsfunc as haf
import finesharp
core = vs.core

opstart = 0

OP = lvf.src(r"[BDMV][Pani Poni Dash][ぱにぽにだっしゅ！]\VOL6\BDMV\STREAM\00007.m2ts")
OP = OP[24:2183]
OP = core.std.CropRel(OP, 20, 20, 8, 6)
OP = fvf.Depth(OP, 16)

OP = core.resize.Spline36(OP, 1280, 720, format=vs.YUV444P16)

def high_dehalo(clip):
	Y_filt = core.knlm.KNLMeansCL(clip, d=0, a=3, h=20)
	Y_filt = haf.FineDehalo(Y_filt, rx=2, ry=4, thmi=250, thma=255, thlimi=64, thlima=100, darkstr=0, brightstr=0, showmask=0, edgeproc=0)
	Y_merge = core.std.MaskedMerge(Y_filt, Y, kgf.retinex_edgemask(Y))
	return Y_merge

def low_dehalo(clip):
	Y_grain = core.knlm.KNLMeansCL(clip, d=0, a=3, h=2)
	Y_dehalo = haf.FineDehalo(Y_grain, rx=2, thmi=250, thma=255, thlimi=64, thlima=100)
	
	Y_mask = kgf.retinex_edgemask(clip).std.Deflate()
	Y_mask = kgf.iterate(Y_mask, core.std.Inflate, 2).std.Maximum().std.Maximum().std.Binarize()
	Y_masked = core.std.MaskedMerge(Y_dehalo, clip, Y_mask)
	return Y_masked

Y, U, V = kgf.split(OP)

op_Ya = low_dehalo(Y)
op_Yb = high_dehalo(Y)
op_Y = fvf.rfs(op_Ya, op_Yb, mappings="[134 140] [146 242] [268 275] [408 541] [777 810] [1334 1541]")
op_Y = fvf.rfs(op_Y, Y, mappings="[543 611]")

op_Ydenoise = lvf.denoise(op_Y, h=30, sigma=40)
op_Ydenoise = fvf.rfs(op_Y, op_Ydenoise, mappings="[1556 1596]")

op_Ysharp = haf.LSFmod(op_Ydenoise, strength=80, soft=10, edgemode=1, Smethod=2, Lmode=2)

op_merge = kgf.join([op_Ysharp, U, V])

op_aa_1 = taa.TAAmbk(op_merge, aatype='Eedi3')
op_aa_2 = taa.TAAmbk(op_merge, aatype='Nnedi3UpscaleSangNom')
op_aa = fvf.rfs(op_aa_1, op_aa_2, mappings="[0 67] [80 132] [146 242] [1315 1466] [1732 1875]")

op_deband = core.f3kdb.Deband(op_aa, range=17, y=40, cb=32, cr=32, grainy=12, grainc=0, output_depth=16)
op_grain = kgf.adaptive_grain(op_deband, 0.5)

op_out = op_grain
final = fvf.Depth(op_out, 10)
final.set_output()