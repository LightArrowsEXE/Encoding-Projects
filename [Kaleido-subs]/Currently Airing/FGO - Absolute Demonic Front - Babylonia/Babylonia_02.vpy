import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import havsfunc as haf
from cooldegrain import *
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

src = fvf.Depth(src, 16)


# Generic filterchain
y, u, v = kgf.split(src)
aa = lvf.upscaled_sraa(y)
aa = kgf.join([aa, u, v])

d_mask = kgf.adaptive_grain(fvf.Depth(src, 16), show_mask=True, luma_scaling=8)
denoise_a = CoolDegrain(aa, tr=1, thsad=72, thsadc=48, bits=16, blksize=8, overlap=4)
denoise_b = CoolDegrain(aa, tr=1, thsad=24, thsadc=48, bits=16, blksize=8, overlap=4)
denoise_c = haf.SMDegrain(aa, tr=2, thSAD=200, RefineMotion=True)
denoise = core.std.MaskedMerge(denoise_a, denoise_b, d_mask)

deband_a = core.f3kdb.Deband(denoise, range=17, y=32, cb=24, cr=24, grainy=48, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(denoise_c, range=5, y=96, cb=88, cr=88, grainy=0, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(deband_b, range=18, y=32, cb=24, cr=24, grainy=64, grainc=0, output_depth=16)
deband = fvf.rfs(deband_a, deband_b, mappings=f"[{opstart+378} {opstart+401}]")

grain = kgf.adaptive_grain(deband, 0.2, luma_scaling=6)


out = grain
final = fvf.Depth(out, 10)
final.set_output()

