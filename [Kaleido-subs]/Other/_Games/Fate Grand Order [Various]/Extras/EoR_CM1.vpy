import vapoursynth as vs
import lvsfunc as lvf
import fvsfunc as fvf
import kagefunc as kgf
import havsfunc as haf
import vsTAAmbk as taa
core = vs.core
core.max_cache_size = 8096

src = lvf.src(r"../[BDMV][Fate／Grand Order -MOONLIGHT／LOSTROOM-]/BDROM/BDMV/STREAM/00002.m2ts")
src = src[24:384]
src = fvf.Depth(src, 16)

denoise = lvf.qden(src, h=1.6)
deband = core.f3kdb.Deband(denoise, range=17, y=40, cb=32, cr=32, grainy=0, grainc=0, output_depth=16)
deband = fvf.rfs(deband, src, "[264 305]")
sharpen = haf.ContraSharpening(deband, src, radius=None, rep=13)

darken = haf.FastLineDarkenMOD(src, strength=72, protection=3, luma_cap=255, threshold=2, thinning=0)
aa = taa.TAAmbk(darken, aatype='Eedi3', opencl=True)

mask = kgf.retinex_edgemask(aa, 0.1)
maskedmerge = core.std.MaskedMerge(sharpen, aa, mask)

out = maskedmerge
final = fvf.Depth(out, 10)
final.set_output()