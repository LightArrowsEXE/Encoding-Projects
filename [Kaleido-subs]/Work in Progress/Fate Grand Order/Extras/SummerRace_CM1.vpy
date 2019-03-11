import vapoursynth as vs
import lvsfunc as lvf
import fvsfunc as fvf
import kagefunc as kgf
import havsfunc as haf
import vsTAAmbk as taa
from nnedi3_rpow2 import nnedi3_rpow2
core = vs.core
core.max_cache_size = 8096

src = lvf.src(r"../[BDMV][Fate／Grand Order -MOONLIGHT／LOSTROOM-]/BDROM/BDMV/STREAM/00010.m2ts")
src = src[24:384]
src = fvf.Depth(src, 16)
Y, U, V = kgf.split(src)

denoise = lvf.qden(src, h=0.4)
deband = core.f3kdb.Deband(denoise, range=17, y=32, cb=24, cr=24, grainy=0, grainc=0, output_depth=16)
contraSharpen = haf.ContraSharpening(deband, src, radius=None, rep=13)

sharpen = haf.LSFmod(src, strength=180, soft=10, edgemode=1, Smethod=2, Lmode=2)
aa = taa.TAAmbk(sharpen, aatype='Eedi3', opencl=True)

mask = kgf.retinex_edgemask(aa, 1)
maskedmerge = core.std.MaskedMerge(contraSharpen, aa, mask)

out = maskedmerge
final = fvf.Depth(out, 10)
final.set_output()