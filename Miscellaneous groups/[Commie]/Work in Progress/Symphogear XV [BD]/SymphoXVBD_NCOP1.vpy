import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import mvsfunc as mvf
from vsutil import *
core = vs.core
core.num_threads = 4


src = lvf.src(r"BDMV/KIXA_90889/BDMV/STREAM/00007.m2ts")
src = src[24:-24]
src = fvf.Depth(src, 32)


scaled = lvf.smart_descale(src, [871, 872, 873],
                           b=0, c=1/2, thresh1=0.02, thresh2=0.4,
                           single_rate_upscale=True,
                           rfactor=3,
                           show_dmask=False)

d_mask = kgf.adaptive_grain(fvf.Depth(scaled, 16), show_mask=True, luma_scaling=8)
denoise_a = mvf.BM3D(scaled, sigma=1.5, depth=16)
denoise_b = mvf.BM3D(scaled, sigma=1.0, depth=16)
denoise = core.std.MaskedMerge(denoise_a, denoise_b, d_mask)

aa = lvf.nneedi3_clamp(denoise)

deband_a = core.f3kdb.Deband(aa, range=18, y=32, cb=24, cr=24, grainy=24, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(aa, range=17, y=40, cb=32, cr=32, grainy=48, grainc=0, output_depth=16)
deband = core.std.MaskedMerge(deband_a, deband_b, d_mask)

grain = kgf.adaptive_grain(deband, 0.15, luma_scaling=8)


out = grain
final = fvf.Depth(out, 10)
final.set_output()
