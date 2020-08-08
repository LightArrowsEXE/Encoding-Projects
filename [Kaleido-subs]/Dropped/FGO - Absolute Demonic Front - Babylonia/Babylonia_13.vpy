import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import mvsfunc as mvf
import havsfunc as haf
from vsutil import *
from cooldegrain import *
core = vs.core
core.num_threads = 3


opstart, edstart = None, 30643


## Importing & Dehardsubbing
src_a = lvf.src('13/Fate Grand Order Absolute Demonic Front Babylonia E13 [1080p][AAC][JapDub][GerSub][Web-DL].mkv')
src_b = lvf.src('13/[Erai-raws] Fate Grand Order - Zettai Majuu Sensen Babylonia - 13 [1080p].mkv')
src_a = src_a+src_a[-1]*2
src_b = src_b[289:]
scomp = lvf.stack_compare(src_a, src_b, height=360, make_diff=True)

hardsubmask = kgf.hardsubmask(src_a, src_b)
src = core.std.MaskedMerge(src_a, src_b, hardsubmask)

src_fade = fvf.Depth(kgf.hardsubmask_fades(src_a, src_b, highpass=1300), 8)
src_fade = core.std.MaskedMerge(src_a, src_b, src_fade)
src = fvf.ReplaceFramesSimple(src, src_fade, mappings=f"[{edstart-96} {src.num_frames-1}]")
scomp2 = lvf.stack_compare(src_a, src, height=360, make_diff=True)

src = fvf.Depth(src, 16)


h = 873
b, c = 1/5, 2/5
math_l, math_c = 0.5 * src.height / h * -1, 0.25 * src.height / h * -1
planes = split(src)
planes[0] = fvf.Depth(planes[0], 32)
descaled = core.fmtc.resample(planes[0], get_w(h), h, kernel='bicubic', a1=b, a2=c, invks=True)
upscaled = core.fmtc.resample(descaled, src.width, src.height, kernel='bicubic', a1=b, a2=c)
credit_mask = core.std.Expr([planes[0], upscaled], 'x y - abs')
credit_mask = kgf.iterate(credit_mask, core.std.Maximum, 4)
credit_mask = kgf.iterate(credit_mask, core.std.Inflate, 2)
credit_mask = fvf.Depth(credit_mask.std.Binarize(0.05), 16)
credit_mask = core.fmtc.resample(credit_mask, sy=math_l)

planes[0] = core.fmtc.resample(fvf.Depth(planes[0], get_depth(src)), get_w(h), h, sy=math_l, kernel='bicubic', a1=b, a2=c, invks=True)
planes[0] = lvf.upscaled_sraa(planes[0], h=src.height, rep=13, rfactor=2.4)
planes[1], planes[2] = [core.resize.Spline36(p, src_top=math_c) for p in planes[1:]]
scaled = fvf.Depth(join(planes), 16)


dehalo = haf.HQDeringmod(scaled, nrmode=2, darkthr=0, sharp=0, mthr=48)
dering = haf.EdgeCleaner(dehalo, strength=6, rmode=13, smode=1, hot=True)
repair = core.rgvs.Repair(dering, scaled, 13)

shift = split(src)
shift[0] = core.fmtc.resample(shift[0], sy=math_l)
shift[1], shift[2] = [core.fmtc.resample(s, sy=math_c) for s in shift[1:]]
src_shift = join(shift)

merge = core.std.MaskedMerge(repair, src_shift, credit_mask)
merge = fvf.rfs(repair, merge, mappings=f"[{edstart-96} {src.num_frames-1}]")
merge = fvf.rfs(repair, merge, mappings=f"[{edstart-96} {src.num_frames-1}]")

d_mask = fvf.Depth(kgf.adaptive_grain(repair, show_mask=True, luma_scaling=4), 16)
denoise_a = mvf.BM3D(merge, sigma=[2,1.5], depth=16, profile1='lc')
denoise_b = CoolDegrain(merge, tr=1, thsad=24, thsadc=48, bits=16, blksize=8, overlap=4)
denoise = core.std.MaskedMerge(denoise_a, denoise_b, d_mask)

deband = core.f3kdb.Deband(denoise, range=14, y=48, cb=40, cr=40, grainy=32, grainc=0, output_depth=16)

grain_a = kgf.adaptive_grain(deband, 0.3, luma_scaling=4)
grain_b = kgf.adaptive_grain(deband, 1.8, luma_scaling=4, static=False)
grain = fvf.rfs(grain_a, grain_b, mappings="[10504 10551] [10738 10785] [11552 11614] [11714 12184] [12239 12343] [12467 12634] [12708 12827] [12888 12929]")

out = grain
final = fvf.Depth(out, 10)
final.set_output()
