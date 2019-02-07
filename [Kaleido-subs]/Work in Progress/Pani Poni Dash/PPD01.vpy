import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import vsTAAmbk as taa
import havsfunc as haf
import finesharp
core = vs.core

opstart = 2158

src = lvf.src(r"[BDMV][Pani Poni Dash][ぱにぽにだっしゅ！]\VOL1\BDMV\STREAM\00005.m2ts")
src = src[24:36466]
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
Y = fvf.rfs(Y_a, Y_b, mappings=f"[{opstart+133} {opstart+140}] [{opstart+241} {opstart+275}] [{opstart+529} {opstart+541}] [30791 30861] [31190 31314]")

Y_sharp = haf.LSFmod(Y, strength=80, soft=10, edgemode=1, Smethod=2, Lmode=2)

Y_mask = kgf.retinex_edgemask(scaled).std.Deflate()
Y_mask = kgf.iterate(Y_mask, core.std.Inflate, 2).std.Maximum().std.Maximum().std.Binarize()
Y_masked = core.std.MaskedMerge(Y, Y_sharp, Y_mask)

Y_masked = Y_sharp
merge = kgf.join([Y_masked, U, V])

aa = taa.TAAmbk(merge, aatype='Eedi3')

deband_a = core.f3kdb.Deband(aa, range=17, y=40, cb=32, cr=32, grainy=12, grainc=0, output_depth=16)
grain_a = kgf.adaptive_grain(deband_a, 0.5)
deband_b = lvf.denoise(aa, h=1)
deband_b = core.f3kdb.Deband(aa, range=18, y=64, cb=56, cr=56, grainy=36, grainc=0, output_depth=16)
grain_b = kgf.adaptive_grain(deband_b, 2)
deband = fvf.rfs(grain_a, grain_b, mappings="[0 722]")



out = deband
final = fvf.Depth(out, 10)
op = scaled[opstart:opstart+2158]
OP = out[opstart:opstart+2158]
opcomp = lvf.comp(op, OP, [50, 140, 241, 274, 276, 477, 534, 571, 625, 715, 809, 909, 992, 1074, 1204, 1512, 1569, 1673, 1892, 2008, 2134])
comp = lvf.comp(scaled, out, [4923, 5272, 6361, 6599, 6932, 7823, 8899, 20409, 30775, 30824, 30887])

test = final[:976]+final[5166:5274]+final[5370:5943]+final[20139:20519]+final[30382:31315]
opcomp.set_output()