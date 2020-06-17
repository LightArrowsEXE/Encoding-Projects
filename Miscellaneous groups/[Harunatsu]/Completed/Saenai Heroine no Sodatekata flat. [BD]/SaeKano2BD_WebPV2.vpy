from functools import partial

import havsfunc as haf
import kagefunc as kgf
import lvsfunc as lvf
import mvsfunc as mvf
import vsTAAmbk as taa
from nnedi3_rpow2 import nnedi3_rpow2
from vsTAAmbk import TAAmbk
from vsutil import depth, get_y, join, plane

import vapoursynth as vs

core = vs.core


upscale_args = dict(height=878, kernel=lvf.kernels.Bicubic(0, 3/5))


src = lvf.src(r"[BDMV]冴えない彼女の育てかた♭Vol.01~Vol.06/[BDMV]冴えない彼女の育てかた♭ VOL.01/BDMV/STREAM/00014.m2ts")[24:1704]
src = depth(src, 32)


descaled = lvf.scale.descale(get_y(src), upscaler=False, mask=False, **upscale_args)

denoised = mvf.BM3D(descaled, sigma=1)
darken = haf.FastLineDarkenMOD(denoised, strength=48, protection=15, luma_cap=130, threshold=4, thinning=0) # some subjective darkening

aa = lvf.util.quick_resample(darken, partial(TAAmbk, aatype='Eedi3'))

upscaled = nnedi3_rpow2(aa, width=src.width, height=src.height)
upscaled = join([upscaled, plane(src, 1), plane(src, 2)])

mask = lvf.scale.descale(get_y(src), mask=False, show_mask=True, **upscale_args)
upscaled = depth(core.std.MaskedMerge(upscaled, src, mask), 16)


deband = core.f3kdb.Deband(upscaled, range=16, y=48, cr=40, cb=40, grainy=12, grainc=0, output_depth=16)

csharp = haf.ContraSharpening(deband, upscaled)

mask = lvf.util.quick_resample(src, kgf.retinex_edgemask)
masked = core.std.MaskedMerge(csharp, upscaled, mask)

grain = kgf.adaptive_grain(masked, 0.3)


out = grain
final = depth(out, 10)
final.set_output()
