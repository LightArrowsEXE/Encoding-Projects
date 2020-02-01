import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import mvsfunc as mvf
import havsfunc as haf
from vsutil import *
from cooldegrain import *
core = vs.core


src = lvf.src(r"BDMV/[BDMV] Fate Grand Order - Absolute Demonic Front Babylonia [Vol.1] [JP]/Disc2/BDMV/STREAM/00008.m2ts")
src = src[24:-24]
src = fvf.Depth(src, 16)


h = 873
b, c = 0, 1/2
planes = split(src)
planes[0] = fvf.Depth(planes[0], 32)
descaled = core.descale.Debicubic(planes[0], get_w(h), h, b, c)
upscaled = core.resize.Bicubic(descaled, src.width, src.height, filter_param_a=b, filter_param_b=c)
credit_mask = core.std.Expr([planes[0], upscaled], 'x y - abs').std.Binarize(0.05)
credit_mask = kgf.iterate(credit_mask, core.std.Maximum, 6)
credit_mask = kgf.iterate(credit_mask, core.std.Inflate, 2)
credit_mask = fvf.Depth(credit_mask, get_depth(src))


aa = lvf.upscaled_sraa(fvf.Depth(src, 16), rfactor=2, h=1080, rep=13, sharp_downscale=False)
darken = haf.FastLineDarkenMOD(aa, strength=32, protection=12, luma_cap=130)
scaled = core.std.MaskedMerge(darken, src, credit_mask)


d_mask = kgf.adaptive_grain(src, show_mask=True, luma_scaling=4)
denoise_a = mvf.BM3D(scaled, sigma=[1.5,1], depth=16, profile1='lc')
denoise_b = CoolDegrain(scaled, tr=1, thsad=24, thsadc=48, bits=16, blksize=8, overlap=4)
denoise = core.std.MaskedMerge(denoise_a, denoise_b, d_mask)

deband = core.f3kdb.Deband(denoise, range=16, y=40, cb=32, cr=32, grainy=24, grainc=0, output_depth=16)
grain = kgf.adaptive_grain(deband, 0.3, luma_scaling=6)


out = grain
final = fvf.Depth(out, 10)
final.set_output()
