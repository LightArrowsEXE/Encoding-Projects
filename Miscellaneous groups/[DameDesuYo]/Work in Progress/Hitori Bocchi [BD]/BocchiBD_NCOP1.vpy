import vapoursynth as vs
import fvsfunc as fvf
import havsfunc as haf
import kagefunc as kgf
import lvsfunc as lvf
import mvsfunc as mvf
import vsTAAmbk as taa
from nnedi3_rpow2 import nnedi3_rpow2
core = vs.core


src = lvf.src(r"BDMV/[BDMV][190724][Hitoribocchi no Marumaru Seikatsu][Vol.1]/BDMV/STREAM/00010.m2ts")
src = core.edgefixer.ContinuityFixer(src, 1, 1, 1, 1, 2)
src = src[24:-24]
src = fvf.Depth(src, 16)


Y, U, V = kgf.split(src)
descale = kgf.inverse_scale(Y, height=810, kernel='bicubic', b=0, c=1)
descale = fvf.Depth(descale, 16)

dehalo = haf.HQDeringmod(descale, nrmode=2, darkthr=0, sharp=0, mthr=56)
aa = taa.TAAmbk(dehalo, aatype='Eedi3', sharp=80, repair=2)

upscale = nnedi3_rpow2(aa).resize.Spline36(1920, 1080)
upscale = kgf.join([upscale, U, V])

denoise = mvf.BM3D(upscale, sigma=[4.5,2.5])
deband = core.f3kdb.Deband(denoise, range=16, y=24, cb=16, cr=16, grainy=24, grainc=0, output_depth=16)
grain = kgf.adaptive_grain(deband, 0.3, luma_scaling=18)


out = deband
final = fvf.Depth(out, 10)
final.set_output()
