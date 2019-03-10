import vapoursynth as vs
import lvsfunc as lvf
import fvsfunc as fvf
import kagefunc as kgf
import havsfunc as haf
import vsTAAmbk as taa
from nnedi3_rpow2 import nnedi3_rpow2
core = vs.core
core.max_cache_size = 8096

src = lvf.src(r"../[BDMV][Fate／Grand Order -MOONLIGHT／LOSTROOM-]/BDROM/BDMV/STREAM/00003.m2ts")
src = src[24:384]
src = fvf.Depth(src, 16)

denoise = lvf.qden(src, h=1)
deband = core.f3kdb.Deband(denoise, range=16, y=32, cb=24, cr=24, grainy=0, grainc=0, output_depth=16)
sharpen = haf.ContraSharpening(deband, src, radius=None, rep=13)

aa_a = taa.TAAmbk(src, aatype='Eedi3', opencl=True)
aa_b = taa.TAAmbk(denoise, aatype='Eedi3SangNom', strenght=0.5, preaa=-1, opencl=True)
aa_b = core.resize.Spline36(aa_b, 1920, 1080)
aa = fvf.rfs(aa_a, aa_b, "[210 263]")

mask = kgf.retinex_edgemask(aa, 1)
maskedmerge = core.std.MaskedMerge(sharpen, aa, mask)


out = maskedmerge
final = fvf.Depth(out, 10)
final.set_output()