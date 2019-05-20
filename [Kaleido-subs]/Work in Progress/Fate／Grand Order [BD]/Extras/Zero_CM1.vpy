import vapoursynth as vs
import lvsfunc as lvf
import fvsfunc as fvf
import kagefunc as kgf
import havsfunc as haf
import vsTAAmbk as taa
from nnedi3_rpow2 import nnedi3_rpow2
core = vs.core
core.max_cache_size = 8096

src = lvf.src(r"../Fate Grand Order -First Order-/BDROM/BDMV/STREAM/00011.m2ts")
src = src[24:383]
src = fvf.Depth(src, 16)

denoise_a = lvf.qden(src, h=1.4, sigma=6)
deband_a = core.f3kdb.Deband(denoise_a, range=18, y=40, cb=32, cr=32, grainy=12, grainc=0, output_depth=16)

denoise_b = lvf.qden(src, h=2, sigma=8)
deband_b = core.f3kdb.Deband(denoise_b, range=21, y=64, cb=56, cr=56, grainy=24, grainc=0, output_depth=16)

deband = fvf.rfs(deband_a, deband_b, mappings="[87 110]")
contraSharpen = haf.ContraSharpening(deband, src, radius=None, rep=13)

sharpen = haf.LSFmod(src, strength=150, soft=10, edgemode=1, Smethod=2, Lmode=2)
aa = taa.TAAmbk(sharpen, aatype='Eedi3', opencl=True)

mask = kgf.retinex_edgemask(aa, 1)
maskedmerge = core.std.MaskedMerge(contraSharpen, aa, mask)

grain = kgf.adaptive_grain(maskedmerge, 1)
grain = fvf.rfs(maskedmerge, grain, mappings="[87 110]")

out = grain
final = fvf.Depth(out, 10)
final.set_output()