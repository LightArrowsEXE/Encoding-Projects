import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import mvsfunc as mvf
import havsfunc as haf
from vsutil import *
from cooldegrain import *
core = vs.core


edstart = 0


src = lvf.src(r"BDMV/[BDMV] Fate Grand Order - Absolute Demonic Front Babylonia [Vol.1] [JP]/Disc2/BDMV/STREAM/00008.m2ts")
src = src[24:-28]
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

d_mask = fvf.Depth(kgf.adaptive_grain(repair, show_mask=True, luma_scaling=4), 16)
denoise_a = mvf.BM3D(repair, sigma=[1,0.5], depth=16, profile1='lc')
denoise_b = CoolDegrain(repair, tr=1, thsad=24, thsadc=48, bits=16, blksize=8, overlap=4)
denoise = core.std.MaskedMerge(denoise_a, denoise_b, d_mask)

deband = core.f3kdb.Deband(denoise, range=15, y=40, cb=32, cr=32, grainy=12, grainc=0, output_depth=16)
grain = kgf.adaptive_grain(deband, 0.3, luma_scaling=4)


out = grain
final = fvf.Depth(out, 10)
final.set_output()
