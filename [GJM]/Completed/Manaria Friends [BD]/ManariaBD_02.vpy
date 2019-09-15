import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import mvsfunc as mvf
from nnedi3_rpow2 import nnedi3_rpow2
from vsTAAmbk import TAAmbk
from vsutil import *
core = vs.core


b, c = 0, 1/2
planes = kgf.split(src)
h, w = get_w(878), 878


# Note: before cutting
preview = 16688
endcard = 16808
part_b = 16928
epend = 20522

# Note: after cutting
edstart = 15586


src = lvf.src(r"BDMV/[BDMV][190302][マナリアフレンズ I]/BD/BDMV/STREAM/00008.m2ts")
blank = core.std.BlankClip(src) # Part B starts too abruptly, so there's some space for a breather after ED.
src = src[24:preview]+blank[:48]+src[part_b:]+src[preview:part_b]


descaled = core.descale.Debicubic(fvf.Depth(planes[0], 32), h, w, b, c)
upscaled = core.resize.Bicubic(descaled, planes[0].width, planes[0].height, filter_param_a=b, filter_param_b=c)
downscaled = core.resize.Spline36(fvf.Depth(src, 32), h, w, format=vs.YUV444PS)

credit_mask = core.std.Expr([fvf.Depth(planes[0], 32), upscaled], 'x y - abs').std.Binarize(0.05)
credit_mask = kgf.iterate(credit_mask, core.std.Maximum, 6)
credit_mask = kgf.iterate(credit_mask, core.std.Inflate, 2)
credit_mask = core.resize.Spline36(credit_mask, h, w)

scaled = fvf.Depth(core.std.MaskedMerge(descaled, kgf.get_y(downscaled), credit_mask), 16)
u = fvf.Depth(core.resize.Bicubic(planes[1], h, w, src_left=0.25), 16)
v = fvf.Depth(core.resize.Bicubic(planes[2], h, w, src_left=0.25), 16)
scaled = kgf.join([scaled, u, v])


aa = TAAmbk(scaled, aatype='Eedi3', repair=2)

deband_a = core.f3kdb.Deband(aa, range=15, y=32, cb=24, cr=24, grainy=12, grainc=0, output_depth=16)
denoise = mvf.BM3D(aa, sigma=[1000,1000]) # w h y y y y
deband_b = core.f3kdb.Deband(denoise, range=4, y=511, cb=511, cr=511, grainy=0, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(deband_b, range=4, y=511, cb=511, cr=511, grainy=0, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(deband_b, range=4, y=511, cb=511, cr=511, grainy=0, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(deband_b, range=31, y=511, cb=511, cr=511, grainy=0, grainc=0, output_depth=16)
deband = fvf.rfs(deband_a, deband_b, mappings="[6522 6605]")

grain = kgf.adaptive_grain(deband, 0.2, luma_scaling=8)


out = grain
final = fvf.Depth(out, 10)
final.set_output()
