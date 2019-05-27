import vapoursynth as vs
import kagefunc as kgf
import vsTAAmbk as taa
import lvsfunc as lvf
import fvsfunc as fvf
import havsfunc as haf
import vsTAAmbk as taa
from nnedi3_rpow2 import nnedi3_rpow2
core = vs.core

opstart = 0

src = lvf.src(r"[BDMV]冴えない彼女の育てかた♭Vol.01~Vol.06/[BDMV]冴えない彼女の育てかた♭ VOL.01/BDMV/STREAM/00009.m2ts")
src = src[24:2184]
src = fvf.Depth(src, 16)


Y, U, V = kgf.split(src)
scaled = kgf.inverse_scale(Y, height=878, kernel='bicubic', b=0, c=3/5)
scaled = fvf.Depth(scaled, 16)

denoised = lvf.quick_denoise(scaled, h=0.4)
darken = haf.FastLineDarkenMOD(denoised, strength=48, protection=15, luma_cap=130, threshold=4, thinning=0) # some subjective darkening

aa_a = taa.TAAmbk(darken, aatype='Eedi3', opencl=True)
aa_b = lvf.NnEedi3(darken)
aa = fvf.rfs(aa_a, aa_b, mappings=f"[{opstart+1276} {opstart+1305}]")

upscaled = nnedi3_rpow2(aa).resize.Spline36(1920, 1080)
upscaled = kgf.join([upscaled, U, V])

deband_low = core.f3kdb.Deband(upscaled, range=16, y=48, cr=40, cb=40, grainy=12, grainc=0, output_depth=16)
deband_high = core.f3kdb.Deband(upscaled, range=18, y=64, cr=56, cb=56, grainy=18, grainc=0, output_depth=16)
deband_higher = core.f3kdb.Deband(upscaled, range=19, y=64, cr=56, cb=56, grainy=24, grainc=0, output_depth=16)
deband_very_high = core.f3kdb.Deband(upscaled, range=7, y=200, cr=192, cb=192, grainy=0, grainc=0, output_depth=16) 
# Don't ever do this unless you *HAVE* to, please - https://slowpics.org/comparison/21b25059-693c-4e2c-8510-e5f141c1faa6
deband_very_high = core.f3kdb.Deband(deband_very_high, range=21, y=72, cr=64, cb=64, grainy=24, grainc=0, output_depth=16)
deband = fvf.rfs(deband_low, upscaled, mappings=f"[{opstart} {opstart+313}] [{opstart+1976} {opstart+2159}]")
deband = fvf.rfs(deband, deband_high, mappings=f"[{opstart+1245} {opstart+1251}] [{opstart+1672} {opstart+1801}]")
deband = fvf.rfs(deband, deband_higher, mappings=f"[{opstart+1078} {opstart+1128}]")
deband = fvf.rfs(deband, deband_very_high, mappings=f"[{opstart+1227} {opstart+1244}]")

sharp = haf.ContraSharpening(deband, upscaled)

mask = kgf.retinex_edgemask(src, sigma=1)
masked = core.std.MaskedMerge(sharp, upscaled, mask)

grain = kgf.adaptive_grain(masked, 0.3)

out = grain
final = fvf.Depth(out, 10)
final.set_output()