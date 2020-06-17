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

opstart = 0


src = lvf.src(r"[BDMV]冴えない彼女の育てかた♭Vol.01~Vol.06/[BDMV]冴えない彼女の育てかた♭ VOL.01/BDMV/STREAM/00009.m2ts")[24:2184]
src = depth(src, 32)


descaled = lvf.scale.descale(get_y(src), upscaler=False, mask=False, **upscale_args)

denoised = mvf.BM3D(descaled, sigma=1)
darken = haf.FastLineDarkenMOD(denoised, strength=48, protection=15, luma_cap=130, threshold=4, thinning=0) # some subjective darkening

aa = lvf.rfs(lvf.util.quick_resample(darken, partial(TAAmbk, aatype='Eedi3')),
             lvf.util.quick_resample(darken, lvf.nneedi3_clamp),
             [(opstart+1276, opstart+1305)])

upscaled = nnedi3_rpow2(aa, width=src.width, height=src.height)
upscaled = join([upscaled, plane(src, 1), plane(src, 2)])

mask = lvf.scale.descale(get_y(src), mask=False, show_mask=True, **upscale_args)
upscaled = depth(core.std.MaskedMerge(upscaled, src, mask), 16)


deband_a = core.f3kdb.Deband(upscaled, range=16, y=48, cr=40, cb=40, grainy=12, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(upscaled, range=18, y=64, cr=56, cb=56, grainy=18, grainc=0, output_depth=16)
deband_c = core.f3kdb.Deband(upscaled, range=19, y=64, cr=56, cb=56, grainy=24, grainc=0, output_depth=16)
deband_d = core.f3kdb.Deband(upscaled, range=7, y=200, cr=192, cb=192, grainy=0, grainc=0, output_depth=16)
# Don't ever do this unless you *HAVE* to, please - https://slowpics.org/comparison/21b25059-693c-4e2c-8510-e5f141c1faa6
deband_d = core.f3kdb.Deband(deband_d, range=21, y=72, cr=64, cb=64, grainy=24, grainc=0, output_depth=16)
deband = lvf.rfs(deband_a, upscaled, ranges=[(opstart, opstart+313), (opstart+1976, opstart+2159)])
deband = lvf.rfs(deband, deband_b, ranges=[(opstart+1245, opstart+1251), (opstart+1672, opstart+1801)])
deband = lvf.rfs(deband, deband_c, ranges=[(opstart+1078, opstart+1128)])
deband = lvf.rfs(deband, deband_d, ranges=[(opstart+1227, opstart+1244)])

csharp = haf.ContraSharpening(deband, upscaled)

mask = lvf.util.quick_resample(src, kgf.retinex_edgemask)
masked = core.std.MaskedMerge(csharp, upscaled, mask)

grain = kgf.adaptive_grain(masked, 0.3)


out = grain
final = depth(out, 10)
final.set_output()
