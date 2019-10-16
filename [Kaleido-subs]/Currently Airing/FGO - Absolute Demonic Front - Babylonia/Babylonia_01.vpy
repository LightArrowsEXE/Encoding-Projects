import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import mvsfunc as mvf
from vsutil import *
from cooldegrain import *
core = vs.core


opstart, edstart = None, 31303


## Importing & Dehardsubbing
src_a = lvf.src('01/Fate Grand Order_ Zettai Majuu Sensen Babylonia - 01 (Wakanim FR 1080p) [!].mkv')
src_b = lvf.src('01/[HorribleSubs] Fate Grand Order - Absolute Demonic Front Babylonia - 01 [1080p].mkv')
src_b = src_b[324:]
scomp = lvf.stack_compare(src_a, src_b, height=480)

hardsubmask = kgf.hardsubmask(src_a, src_b)
src = core.std.MaskedMerge(src_a, src_b, hardsubmask)

src_fade = fvf.Depth(kgf.hardsubmask_fades(src_a, src_b, highpass=1300), 8)
src_fade = core.std.MaskedMerge(src_a, src_b, src_fade)
src = fvf.ReplaceFramesSimple(src, src_fade, mappings="[0 120] [2581 2674]")

src = fvf.Depth(src, 16)


# Generic filterchain
y, u, v = kgf.split(src)
aa = lvf.upscaled_sraa(y)
aa = kgf.join([aa, u, v])

d_mask = kgf.adaptive_grain(fvf.Depth(src, 16), show_mask=True, luma_scaling=6)
denoise_a = CoolDegrain(aa, tr=1, thsad=72, thsadc=48, bits=16, blksize=8, overlap=4)
denoise_b = CoolDegrain(aa, tr=1, thsad=24, thsadc=48, bits=16, blksize=8, overlap=4)
denoise = core.std.MaskedMerge(denoise_a, denoise_b, d_mask)

deband = core.f3kdb.Deband(denoise, range=17, y=32, cb=24, cr=24, grainy=48, grainc=0, output_depth=16)

grain = kgf.adaptive_grain(deband, 0.2, luma_scaling=6)
merge = fvf.rfs(grain, src, mappings="[31303 33470]")


out = merge
final = fvf.Depth(out, 10)
final.set_output()
