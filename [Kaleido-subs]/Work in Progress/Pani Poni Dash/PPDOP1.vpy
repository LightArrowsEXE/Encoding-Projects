import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import vsTAAmbk as taa
import havsfunc as haf
import finesharp
core = vs.core

opstart = 0

src = lvf.src(r"[BDMV][Pani Poni Dash][ぱにぽにだっしゅ！]\VOL6\BDMV\STREAM\00007.m2ts")
src = src[24:2183]
src = core.std.CropRel(src, 20, 20, 8, 6)
src = fvf.Depth(src, 16)

scaled = core.resize.Spline36(src, 1280, 720, format=vs.YUV444P16)
Y, U, V = kgf.split(scaled)
Y_copy = Y

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

Y_a = low_dehalo(Y)
Y_b = high_dehalo(Y)
Y = fvf.rfs(Y_a, Y_b, mappings=f"[{opstart+133} {opstart+140}] [{opstart+146} {opstart+242}] [{opstart+268} {opstart+275}] [{opstart+408} {opstart+541}] [{opstart+777} {opstart+810}] [{opstart+1334} {opstart+1541}]")
Y = fvf.rfs(Y, Y_copy, mappings=f"[{opstart+543} {opstart+611}]")

Y_denoise = lvf.denoise(Y, h=30, sigma=40)
Y_denoise = fvf.rfs(Y, Y_denoise, mappings=f"[{opstart+1556} {opstart+1596}]")

Y_sharp = haf.LSFmod(Y_denoise, strength=80, soft=10, edgemode=1, Smethod=2, Lmode=2)

merge_1 = kgf.join([Y_sharp, U, V])
merge_2 = kgf.join([Y_sharp, U, V])
merge = fvf.rfs(merge_1, merge_2, mappings=f"[{opstart+543} {opstart+611}] [{opstart+777} {opstart+810}] [{opstart+1556} {opstart+1596}]")

aa_1 = taa.TAAmbk(merge, aatype='Eedi3')
aa_2 = taa.TAAmbk(merge, aatype=4)
aa = fvf.rfs(aa_1, aa_2, mappings=f"[{opstart} {opstart+67}] [{opstart+80} {opstart+132}] [{opstart+146} {opstart+242}] [{opstart+1315} {opstart+1466}] [{opstart+1732} {opstart+1875}]")

deband = core.f3kdb.Deband(aa, range=17, y=40, cb=32, cr=32, grainy=12, grainc=0, output_depth=16)
grain = kgf.adaptive_grain(deband, 0.5)

out = grain
final = fvf.Depth(out, 10)
opcomp = lvf.comp(scaled, out, [50, 140, 241, 274, 276, 477, 534, 571, 625, 715, 809, 909, 992, 1074, 1204, 1315, 1466, 1512, 1569, 1673, 1892, 2008, 2134])
final.set_output()