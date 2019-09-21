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
h, w = get_w(878), 878


src = lvf.src(r"BDMV/[BDMV][190402][マナリアフレンズ II]/BD/BDMV/STREAM/00012.m2ts")
src = src[24:982+24]


planes = kgf.split(src)
descaled = fvf.Depth(core.descale.Debicubic(fvf.Depth(planes[0], 32), h, w, b, c), 16)
u = fvf.Depth(core.resize.Bicubic(planes[1], h, w, src_left=0.25), 16)
v = fvf.Depth(core.resize.Bicubic(planes[2], h, w, src_left=0.25), 16)
scaled = kgf.join([descaled, u, v])


aa = TAAmbk(scaled, aatype='Eedi3', repair=2)

deband = core.f3kdb.Deband(aa, range=15, y=32, cb=24, cr=24, grainy=12, grainc=0, output_depth=16)
grain = kgf.adaptive_grain(deband, 0.2, luma_scaling=8)


out = grain
final = fvf.Depth(out, 10)
final.set_output()
