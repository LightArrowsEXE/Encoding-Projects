import vapoursynth as vs
import kagefunc as kgf
import vsTAAmbk as taa
import lvsfunc as lvf
import fvsfunc as fvf
import havsfunc as haf
import vsTAAmbk as taa
import mvsfunc as mvf
from nnedi3_rpow2 import nnedi3_rpow2
core = vs.core

src = lvf.src(r"[BDMV]冴えない彼女の育てかた♭Vol.01~Vol.06/[BDMV]冴えない彼女の育てかた♭ VOL.01/BDMV/STREAM/00014.m2ts")
src = src[24:1704]
src = fvf.Depth(src, 16)


Y, U, V = kgf.split(src)
scaled = kgf.inverse_scale(Y, height=878, kernel='bicubic', b=0, c=3/5, mask_detail=True)
scaled = fvf.Depth(scaled, 16)

denoised = mvf.BM3D(scaled, sigma=1)
darken = haf.FastLineDarkenMOD(denoised, strength=48, protection=15, luma_cap=130, threshold=4, thinning=0) # some subjective darkening

aa = taa.TAAmbk(darken, aatype='Eedi3')

upscaled = nnedi3_rpow2(aa).resize.Spline36(1920, 1080)
upscaled = kgf.join([upscaled, U, V])

deband = core.f3kdb.Deband(upscaled, range=16, y=48, cr=40, cb=40, grainy=12, grainc=0, output_depth=16)

sharp = haf.ContraSharpening(deband, upscaled)

mask = kgf.retinex_edgemask(src)
masked = core.std.MaskedMerge(sharp, upscaled, mask)

grain = kgf.adaptive_grain(masked, 0.3)


out = grain
final = fvf.Depth(out, 10)
final.set_output()