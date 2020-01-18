import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import havsfunc as haf
import mvsfunc as mvf
from vsTAAmbk import TAAmbk
from vsutil import *
from nnedi3_rpow2 import *
from cooldegrain import *
core = vs.core

opstart = 1534


src = lvf.src(r'BDMV/HIGURASHI_BD/00016.m2ts')
src = lvf.decomb(src, TFF=True, vinv=False)
src = src[:-24]
crop = core.std.CropAbs(src, x=4, y=0, width=712, height=480)
crop = fvf.Depth(crop, 32)


planes = split(crop)
planes[0] = nnedi3_rpow2(planes[0]).resize.Spline36(get_w(484, 20/11), 484)
planes[1], planes[2] = [core.resize.Bicubic(p, planes[0].width/2, planes[0].height/2) for p in planes[1:]]
scaled = fvf.Depth(join(planes), 16)


contra = haf.ContraSharpening(scaled, core.resize.Spline36(crop, scaled.width, scaled.height, format=scaled.format), 18)
aa = TAAmbk(contra, aatype='Eedi3', repair=2)
dering = haf.EdgeCleaner(aa, strength=14, rmode=3, smode=1, hot=True)

d_mask = kgf.adaptive_grain(dering, show_mask=True, luma_scaling=6)
denoise_a = CoolDegrain(dering, tr=1, thsad=72, thsadc=48, bits=16, blksize=8, overlap=4)
denoise_b = CoolDegrain(dering, tr=1, thsad=24, thsadc=48, bits=16, blksize=8, overlap=4)
denoise = core.std.MaskedMerge(denoise_a, denoise_b, d_mask)

den_diff = mvf.BM3D(dering, sigma=[20,0], depth=16, profile1='lc')
deb_diff = core.f3kdb.Deband(dering, range=6, y=128, cr=128, cb=128, grainy=0, grainc=0, output_depth=16)
deb_diff = core.f3kdb.Deband(deb_diff, range=14, y=64, cr=64, cb=64, grainy=72, grainc=0, output_depth=16)
diff = core.std.MakeDiff(denoise, den_diff)

deband_a = core.f3kdb.Deband(denoise, range=15, preset="medium/nograin", output_depth=16)
deband_b = core.std.MergeDiff(diff, deb_diff)
deband = fvf.rfs(deband_a, deband_b, mappings=f"[{opstart+1032} {opstart+1178}]")

grain = kgf.adaptive_grain(deband, 0.1, luma_scaling=6)


out = grain
final = fvf.Depth(out, 10)
final.set_output()
