import vapoursynth as vs
import lvsfunc as lvf
import fvsfunc as fvf
import kagefunc as kgf
import havsfunc as haf
import vsTAAmbk as taa
from nnedi3_rpow2 import nnedi3_rpow2
core = vs.core
core.max_cache_size = 8096

src_a = lvf.src(r"../Fate Grand Order -First Order-/BDROM/BDMV/STREAM/00001.m2ts")
src_a = src_a[24:2304]
src_a = fvf.Depth(src_a, 16)

src_b = lvf.src(r"../FATE GRAND ORDER FIRST ORDER German BDMV/BDMV/STREAM/00007.m2ts")
src_b = src_b[48:2328]
src_b = fvf.Depth(src_b, 16)

src = src_a[:1062]+src_b[1062:1132]+src_a[1132:]

denoise = lvf.qden(src, mode=3, sigma=8, sbsize=24)
deband = core.f3kdb.Deband(denoise, range=21, y=64, cb=56, cr=56, grainy=24, grainc=0, output_depth=16)
contraSharpen = haf.ContraSharpening(deband, src, radius=None, rep=13)

aa = taa.TAAmbk(src, aatype='Eedi3', opencl=True)

mask = kgf.retinex_edgemask(aa, 1)
maskedmerge = core.std.MaskedMerge(contraSharpen, aa, mask)

out = maskedmerge
final = fvf.Depth(out, 10)
comp = lvf.comp(src, out, [40, 160, 270, 400, 540, 700, 850, 920, 940, 1040, 1080, 1131, 1250, 1352, 1382, 1401, 1469, 1590, 1682, 1700, 1800, 1900, 2000, 2050, 2100, 2150, 2200, 2250])
final.set_output()