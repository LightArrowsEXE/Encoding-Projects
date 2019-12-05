import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import mvsfunc as mvf
import havsfunc as haf
from vsTAAmbk import *
core = vs.core

edstart = 0

src = lvf.src(r'BDMV/[BDMV][191002][Machikado Mazoku][Vol.1]/MACHIKADO_MAZOKU_1/BDMV/STREAM/00019.m2ts')
src = src[:-24]
src = fvf.Depth(src, 16)


scaled = lvf.smart_descale(src, [958, 980],
                           b=0, c=1/2, thresh1=0.02, thresh2=0.4,
                           show_dmask=False)

l_mask = kgf.retinex_edgemask(src, 1).std.Binarize().std.Inflate().std.Maximum()
ref = core.knlm.KNLMeansCL(src, d=2, h=4)
denoise = mvf.BM3D(src, sigma=[1.25, 1], depth=16, ref=ref, profile1='fast')
csharp = haf.ContraSharpening(denoise, src)
masked = core.std.MaskedMerge(csharp, src, l_mask)

aa_a = TAAmbk(masked, aatype='Nnedi3')
aa_b = lvf.upscaled_sraa(masked)
aa = fvf.rfs(aa_a, aa_b, mappings=f"[{edstart+1965} {edstart+2159}]")

deband = core.f3kdb.Deband(aa, range=18, output_depth=16, preset="medium/nograin")
grain = kgf.adaptive_grain(deband, 0.15, luma_scaling=16)


out = grain
final = fvf.Depth(out, 10)
final.set_output()
