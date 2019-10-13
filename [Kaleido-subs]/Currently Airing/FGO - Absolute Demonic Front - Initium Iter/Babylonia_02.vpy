import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import mvsfunc as mvf
from vsTAAmbk import TAAmbk
from vsutil import *
from nnedi3_rpow2 import nnedi3_rpow2
core = vs.core


opstart, edstart = 1918, 31889


## Importing & Dehardsubbing
src_a = lvf.src('02/Fate Grand Order Absolute Demonic Front Babylonia E02 [1080p][AAC][JapDub][GerSub][Web-DL].mkv')
src_b = lvf.src('02/[HorribleSubs] Fate Grand Order - Absolute Demonic Front Babylonia - 02 [1080p].mkv')
src_b = src_b[289:]
scomp = lvf.stack_compare(src_a, src_b, height=480)

hardsubmask = kgf.hardsubmask(src_a, src_b)
src = core.std.MaskedMerge(src_a, src_b, hardsubmask)

src_fade = fvf.Depth(kgf.hardsubmask_fades(src_a, src_b, highpass=1300), 8)
src_fade = core.std.MaskedMerge(src_a, src_b, src_fade)
src = fvf.ReplaceFramesSimple(src, src_fade, mappings=f"[{edstart-96} {edstart-1}]")
scomp2 = lvf.stack_compare(src_a, src, height=480)

src = fvf.Depth(src, 32)

### Scaling
y, u, v = kgf.split(src)
b, c = 1/3, 1/3
descaled = core.descale.Debicubic(y, get_w(873), 873, b=b, c=c)
upscaled = core.resize.Bicubic(descaled, src.width, src.height, filter_param_a=b, filter_param_b=c)
credit_mask = core.std.Expr([fvf.Depth(y, 32), upscaled], 'x y - abs').std.Binarize(0.05)
credit_mask = kgf.iterate(credit_mask, core.std.Maximum, 6)
credit_mask = kgf.iterate(credit_mask, core.std.Inflate, 2)

aa = fvf.Depth(TAAmbk(fvf.Depth(descaled, 16), aatype='Eedi3', repair=2), 32)

scaled = nnedi3_rpow2(aa).resize.Bicubic(src.width, src.height)
scaled = core.std.MaskedMerge(scaled, y, credit_mask)
scaled = kgf.join([scaled, u, v])


# Generic filterchain
denoise = fvf.Depth(mvf.BM3D(scaled, sigma=[1.5,0.5]), 16)

d_mask = kgf.adaptive_grain(fvf.Depth(src, 16), show_mask=True, luma_scaling=6)
deband_a = core.f3kdb.Deband(denoise, range=16, y=32, cb=24, cr=24, grainy=24, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(denoise, range=18, y=40, cb=32, cr=32, grainy=48, grainc=0, output_depth=16)
deband = core.std.MaskedMerge(deband_a, deband_b, d_mask)

grain = kgf.adaptive_grain(deband, 0.3, luma_scaling=6)


out = grain
final = fvf.Depth(out, 10)
final[opstart:opstart+2159].set_output()
