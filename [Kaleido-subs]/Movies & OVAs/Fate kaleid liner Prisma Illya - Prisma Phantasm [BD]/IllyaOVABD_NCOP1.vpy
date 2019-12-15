import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import havsfunc as haf
import mvsfunc as mvf
from cooldegrain import *
from vsutil import *
core = vs.core


src = lvf.src(r"BDMV/PRISMAPHANTASM/BDMV/STREAM/00005.m2ts")
src = src[24:-24]
shift = haf.FixChromaBleedingMod(src, cx=.25, cy=0, thr=100, strength=1, blur=True)
shift = fvf.Depth(shift, 32)


planes = split(shift)
planes[0] = lvf.upscaled_sraa(planes[0], h=720, rfactor=3)
planes[1], planes[2] = [core.resize.Bicubic(p, planes[0].width, planes[0].height) for p in planes[1:]]
aa = join(planes)


denoise = mvf.BM3D(aa, sigma=2, depth=16)
deband = core.f3kdb.Deband(denoise, range=19, preset="medium", output_depth=16)
grain = kgf.adaptive_grain(deband, 0.3, luma_scaling=6)


out = grain
final = fvf.Depth(out, 10)
final.set_output()