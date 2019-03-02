import vapoursynth as vs
import kagefunc as kgf
import vsTAAmbk as taa
import lvsfunc as lvf
import fvsfunc as fvf
import havsfunc as haf
core = vs.core

src = lvf.src(r"[BDMV]冴えない彼女の育てかた♭Vol.01~Vol.06/[BDMV]冴えない彼女の育てかた♭ VOL.01/BDMV/STREAM/00013.m2ts")
src = src[24:1768]
src = fvf.Depth(src, 16)

denoised = lvf.qden(src, h=0.4)
denoised = haf.ContraSharpening(denoised, src)

aa = taa.TAAmbk(denoised, aatype='Eedi3', opencl=True)

deband = core.f3kdb.Deband(aa, range=16, y=48, cr=40, cb=40, grainy=12, grainc=0, output_depth=16)

mask = kgf.retinex_edgemask(src, sigma=1)
masked = core.std.MaskedMerge(deband, aa, mask)

grain = kgf.adaptive_grain(masked, 0.1)

out = grain

final = fvf.Depth(out, 10)
final.set_output()