import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import mvsfunc as mvf
from vsTAAmbk import TAAmbk
core = vs.core


## Importing & Dehardsubbing
src_a = lvf.src('02/Val x Love - 02 (AoD 1080p+).mkv')
src_b = lvf.src('02/[Erai-raws] Val x Love - 02 [1080p].mkv')
#src_b = src_b[289:]
scomp = lvf.stack_compare(src_a, src_b, height=480)

hardsubmask = kgf.hardsubmask(src_a, src_b)
src = core.std.MaskedMerge(src_a, src_b, hardsubmask)

src_fade = fvf.Depth(kgf.hardsubmask_fades(src_a, src_b, highpass=1300), 8)
src_fade = core.std.MaskedMerge(src_a, src_b, src_fade)
src = fvf.ReplaceFramesSimple(src, src_fade, mappings=f"")
scomp2 = lvf.stack_compare(src_a, src, height=480)

src = fvf.Depth(src, 16)
src = src[24:-33]

denoise = mvf.BM3D(src, sigma=[1.5,0.8])
aa = TAAmbk(denoise, aatype='Nnedi3')
deband = core.f3kdb.Deband(aa, range=18, y=32, cb=24, cr=24, grainy=36, grainc=0, output_depth=16)
grain = kgf.adaptive_grain(deband, 0.3, luma_scaling=10)


out = grain
final = fvf.Depth(out, 10)
final.set_output()
