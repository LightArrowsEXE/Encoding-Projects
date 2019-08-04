import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import vsTAAmbk as taa
from nnedi3_rpow2 import nnedi3_rpow2
core = vs.core

# Notes: awful source. It can only be saved so much, and I honest to God hope 
# there's better sources coming sooner or later. BDs fucking where?

src_a = lvf.src(r"G:/src/Fate Grand Order_ Zettai Majuu Sensen Babylonia - 00 (Wakanim SC 1080p).mkv")
src_a = fvf.Depth(src_a, 16) # Hardsubbed dialogue, better overall quality
src_b = lvf.src(r"G:/src/Fate Grand Order_ Zettai Majuu Sensen Babylonia - 00 (Wakanim RU 1080p).mkv")
src_b = fvf.Depth(src_b, 16) # Hardsubbed credits in ED
mask = kgf.hardsubmask(src_a, src_b)
src = core.std.MaskedMerge(src_a, src_b, mask)

src = fvf.rfs(src, src_a, mappings="[35940 38105]")
src = fvf.Depth(src, 16)


Y, U, V = kgf.split(src)
scaled = kgf.inverse_scale(Y, height=873, kernel='bicubic', b=0, c=1/2)
scaled = fvf.Depth(scaled, 16) # Just descaling to AA this a bit stronger
aa = taa.TAAmbk(scaled, aatype='Eedi3', cycle=2)
scaled = nnedi3_rpow2(aa).resize.Spline36(src.width, src.height)
scaled = kgf.join([scaled, U, V])

deband = core.f3kdb.Deband(scaled, range=17, y=40, cb=32, cr=32, grainy=36, grainc=0, output_depth=16)
grain = kgf.adaptive_grain(deband, 0.3, luma_scaling=4)


out = grain
final = fvf.Depth(out, 10)
final.set_output()
