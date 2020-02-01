import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import mvsfunc as mvf
import havsfunc as haf
from vsutil import *
from cooldegrain import *
core = vs.core


opstart = 1918
op_sf_a = f"[{opstart+378} {opstart+401}]"
op_sf_b = f"[{opstart+1728} {opstart+1757}]"


src = lvf.src(r"BDMV/[BDMV] Fate Grand Order - Absolute Demonic Front Babylonia [Vol.1] [JP]/Disc2/BDMV/STREAM/00000.m2ts")
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


# A lot of subjective filtering here. Babylonia's BDs ain't good, and descaling does not fix the awful lineart.
# upscaled_sraa does not appear to work either if I descale and reupscale with it.
# Here we're doing subjective sharpening, followed by dehaloing (due to sharpening + upscaled_sraa being prone
# to introducing a lot of halo), followed up by some linedarkening. We also repair the dehalo'd clip with
# the src so we don't murder too many lines too badly.
aa = lvf.upscaled_sraa(fvf.Depth(src, 16), rfactor=2, h=1080, sharp_downscale=False)
sharp = haf.LSFmod(aa, strength=120, soft=10, edgemode=1, Smethod=2, Lmode=2)
dehalo = haf.HQDeringmod(sharp, nrmode=2, darkthr=0, sharp=0, mthr=32)
repair = core.rgvs.Repair(dehalo, fvf.Depth(src, 16), 13)
darken = haf.FastLineDarkenMOD(repair, strength=48, protection=12, luma_cap=130)
scaled = core.std.MaskedMerge(darken, src, credit_mask)


d_mask = kgf.adaptive_grain(src, show_mask=True, luma_scaling=4)
denoise_a = mvf.BM3D(scaled, sigma=[1,0.5], depth=16, profile1='lc')
denoise_b = CoolDegrain(scaled, tr=1, thsad=24, thsadc=48, bits=16, blksize=8, overlap=4)
denoise = core.std.MaskedMerge(denoise_a, denoise_b, d_mask)
denoise = fvf.rfs(denoise, denoise_a, mappings=op_sf_a)

deband_a = core.f3kdb.Deband(denoise, range=16, y=40, cb=32, cr=32, grainy=24, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(denoise, range=6, y=72, cb=64, cr=64, grainy=0, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(deband_b, range=14, y=48, cb=40, cr=40, grainy=24, grainc=0, output_depth=16)
deband_c = core.f3kdb.Deband(denoise, range=12, y=56, cb=48, cr=48, grainy=36, grainc=0, output_depth=16)
deband = fvf.rfs(deband_a, deband_b, mappings=op_sf_a)
deband = fvf.rfs(deband, deband_c, mappings=op_sf_b)

grain = kgf.adaptive_grain(deband, 0.5, luma_scaling=4)


out = grain
final = fvf.Depth(out, 10)
final.set_output()
