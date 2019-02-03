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

scaled = core.resize.Spline36(src, 1024, 576, format=vs.YUV444P16)
dehalo = haf.YAHR(scaled, blur=4, depth=64)

denoise_a = lvf.denoise(dehalo, h=0.3)
dbn_a = core.f3kdb.Deband(denoise_a, range=18, y=48, cb=40, cr=40, grainy=0, grainc=0, output_depth=16)

denoise_b = lvf.denoise(scaled, h=1.4)
dbn_b = core.f3kdb.Deband(denoise_b, range=18, y=48, cb=40, cr=40, grainy=0, grainc=0, output_depth=16)

mask = kgf.retinex_edgemask(scaled, 1)
aa = taa.TAAmbk(scaled, aatype='Eedi3', opencl=True)
masked = core.std.MaskedMerge(dbn_a, aa, mask)

masked = fvf.rfs(masked, dbn_b, mappings=f"[{opstart+1049} {opstart+1313}]")

darken = haf.FastLineDarkenMOD(masked, strength=24)

grain = kgf.adaptive_grain(darken, 1)

out = grain
final = fvf.Depth(out, 10)
op = scaled[opstart:opstart+2158]
OP = out[opstart:opstart+2158]
comp = lvf.comp(scaled, out, [8964,5183,21697,22117,4405,20756,31248,15989,29566,35694,18303,35275,27664,20628,33435,9925,29152,3015,25913,25421,23927,15814,10901,21151,13453,11276,28444,20043,26837,21286,9696,28695,17389,10806,23680,23520,30824,24907,31658,19550,7224,22109,33000,27859,34855,21985,4730,11913,1904,31429]) #random number generated frames are fun, right?
opcomp = lvf.comp(op, OP, [50, 274, 477, 571, 625, 715, 809, 909, 992, 1074, 1204, 1512, 1569, 1673, 1892, 2134])
comp.set_output()