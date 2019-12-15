import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import havsfunc as haf
import mvsfunc as mvf
from cooldegrain import *
from vsutil import *
core = vs.core


src = lvf.src(r"BDMV/PRISMAPHANTASM/BDMV/STREAM/00004.m2ts")
src = src[24:-24]
ef = core.edgefixer.ContinuityFixer(src, 1, 1, 1, 1)
shift = haf.FixChromaBleedingMod(ef, cx=.25, cy=0, thr=100, strength=1, blur=True)
shift = fvf.Depth(shift, 32)


planes = split(shift)
planes[0] = lvf.upscaled_sraa(planes[0], h=720, rfactor=3)
planes[1], planes[2] = [core.resize.Bicubic(p, planes[0].width, planes[0].height) for p in planes[1:]]
aa = join(planes)

denoise = mvf.BM3D(aa, sigma=2, depth=16)
make_diff = core.std.MakeDiff(fvf.Depth(aa, get_depth(denoise)), denoise)

deband = core.f3kdb.Deband(denoise, range=18, preset="medium", output_depth=16)
merge_diff = core.std.MergeDiff(deband, make_diff)

grain = kgf.adaptive_grain(merge_diff, 0.1, luma_scaling=6)


out = grain
final = fvf.Depth(out, 10)
final.set_output()
