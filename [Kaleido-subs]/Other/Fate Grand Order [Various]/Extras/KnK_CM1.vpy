import vapoursynth as vs
import lvsfunc as lvf
import fvsfunc as fvf
import kagefunc as kgf
import havsfunc as haf
import vsTAAmbk as taa
from nnedi3_rpow2 import nnedi3_rpow2
core = vs.core
core.max_cache_size = 8096

src = lvf.src(r"../Fate Grand Order -First Order-/BDROM/BDMV/STREAM/00009.m2ts")
src = src[24:384]
src = fvf.Depth(src, 16)

denoise = lvf.qden(src, h=0.4, sigma=2)
deband = core.f3kdb.Deband(denoise, range=18, y=40, cb=32, cr=32, grainy=12, grainc=0, output_depth=16)
contraSharpen = haf.ContraSharpening(deband, src, radius=None, rep=13)

sharpen = haf.LSFmod(src, strength=100, soft=10, edgemode=1, Smethod=2, Lmode=2)
aa_a = taa.TAAmbk(sharpen, aatype='Eedi3', opencl=True)
aa_b = taa.TAAmbk(sharpen, aatype='Eedi3SangNom', opencl=True)
aa = fvf.rfs(aa_a, aa_b, mappings='[244 275]')

mask = kgf.retinex_edgemask(aa, 1)
maskedmerge = core.std.MaskedMerge(contraSharpen, aa, mask)

grain = kgf.adaptive_grain(maskedmerge, 0.5, luma_scaling=8)

out = grain
final = fvf.Depth(out, 10)
comp = lvf.comp(src, out, [90, 107, 275])
final.set_output()