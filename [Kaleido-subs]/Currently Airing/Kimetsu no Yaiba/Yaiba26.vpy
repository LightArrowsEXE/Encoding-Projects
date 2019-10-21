import vapoursynth as vs
import fvsfunc as fvf
import kagefunc as kgf
import lvsfunc as lvf
import mvsfunc as mvf
import vsTAAmbk as taa
from nnedi3_rpow2 import nnedi3_rpow2
core = vs.core

opstart, edstart = None, None

src_a = lvf.src(r"26/Demon Slayer Kimetsu no Yaiba E26 [1080p][AAC][JapDub][GerSub][Web-DL].mkv")
src_b = lvf.src(r"26/[Erai-raws] Kimetsu no Yaiba - 26 END [1080p][Multiple Subtitle].mkv")
src_b = src_b[1:]
scomp = lvf.scomp(src_a, src_b, height=360, make_diff=True) # Matching

hardsubmask = kgf.hardsubmask(src_a, src_b)
src = core.std.MaskedMerge(src_a, src_b, hardsubmask)

src_fade = fvf.Depth(kgf.hardsubmask_fades(src_a, src_b, highpass=1300), 8)
src_fade = core.std.MaskedMerge(src_a, src_b, src_fade)
src = fvf.ReplaceFramesSimple(src, src_fade, mappings=f"[1103 1246] [34093 34096] [34667 34764]")
scomp2 = lvf.scomp(src_b, src, height=360, make_diff=True) 
src = fvf.Depth(src, 16)


Y, U, V = kgf.split(src)
descaled = kgf.inverse_scale(Y, height=855, kernel='bicubic', b=0.2, c=0.4, mask_detail=True, descale_mask_zones=f"[31884 33888]")
descaled = fvf.Depth(descaled, 16)

aa = taa.TAAmbk(descaled, aatype='Nnedi3')

scaled = nnedi3_rpow2(aa).resize.Spline36(1920, 1080)
scaled = kgf.join([scaled, U, V])


deband = core.f3kdb.Deband(scaled, range=18, y=40, cb=32, cr=32, grainy=12, grainc=0, output_depth=16)
grain = kgf.adaptive_grain(deband, 0.3)


final = fvf.Depth(grain, 10)
final.set_output()
