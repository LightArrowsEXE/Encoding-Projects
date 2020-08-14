import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import mvsfunc as mvf
import havsfunc as haf
from vsutil import *
from nnedi3_rpow2 import *
core = vs.core


src_a = lvf.src(r"05/22 7  E05 [1080p][AAC][JapDub][GerSub][Web-DL].mkv")
src_b = lvf.src(r"05/[Erai-raws] 22-7 - 05 [1080p].mkv")
blank = core.std.BlankClip(src_a)[0]
src_a = src_a[0]+src_a[:16975]+src_a[16974]*48+src_a[16975]*2+src_a[16976:]
src_b = src_b[289:]#+blank
scomp = lvf.scomp(src_a, src_b, height=360, make_diff=True)


hardsubmask = kgf.hardsubmask(src_a, src_b)
src = core.std.MaskedMerge(src_a, src_b, hardsubmask)

hardsubmask_fade = fvf.Depth(kgf.hardsubmask_fades(src_a, src_b, highpass=1200), 8)
src_fade = core.std.MaskedMerge(src_a, src_b, hardsubmask_fade)
src = fvf.rfs(src, src_fade, mappings=f"[1265 1323] [3692 3772] [8209 8212] [19463 19466] [19484 19486] [21190 21240] [23596 23663] [33837 33840] [33931 33935]")
src = fvf.rfs(src, src_b, mappings=f"[{src_a.num_frames-121} {src_a.num_frames-1}]")
scomp2 = lvf.scomp(src, src_b, height=360, make_diff=True)


ef = core.edgefixer.ContinuityFixer(src, 1, 1, 1, 1)
ef = fvf.Depth(ef, 32)


h = 900
b, c =  1/5, 2/5
planes = split(ef)
descaled = core.descale.Debicubic(planes[0], get_w(h), h, b, c)
upscaled = core.resize.Bicubic(descaled, planes[0].width, planes[0].height, filter_param_a=b, filter_param_b=c)
credit_mask = core.std.Expr([planes[0], upscaled], 'x y - abs').std.Binarize(0.05)
credit_mask = kgf.iterate(credit_mask, core.std.Maximum, 6)
credit_mask = kgf.iterate(credit_mask, core.std.Inflate, 2)

descaled = nnedi3_rpow2(descaled).resize.Spline36(planes[0].width, planes[0].height)
planes[0] = core.std.MaskedMerge(descaled, planes[0], credit_mask)
scaled = join(planes)


debl = fvf.Depth(core.deblock.Deblock(scaled, quant=18), 16)
dering = haf.EdgeCleaner(debl, strength=2, rmode=13, smode=1)
deband = core.f3kdb.Deband(dering, range=16, y=32, cb=24, cr=24, grainy=12, grainc=0, output_depth=16)
grain = kgf.adaptive_grain(deband, 0.1, luma_scaling=6)


out = grain
final = fvf.Depth(out, 10)
final.set_output()
