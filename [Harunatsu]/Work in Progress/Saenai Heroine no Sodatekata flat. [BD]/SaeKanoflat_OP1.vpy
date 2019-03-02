import vapoursynth as vs
import kagefunc as kgf
import vsTAAmbk as taa
import lvsfunc as lvf
import fvsfunc as fvf
import havsfunc as haf
core = vs.core

src_op = lvf.src(r"[BDMV]冴えない彼女の育てかた♭Vol.01~Vol.06/[BDMV]冴えない彼女の育てかた♭ VOL.01/BDMV/STREAM/00009.m2ts")
src_op = src_op[24:2184]
src_op = fvf.Depth(src_op, 16)

op_denoised = lvf.denoise(src_op, h=0.4)
op_denoised = haf.ContraSharpening(op_denoised, src_op)

op_aa_a = taa.TAAmbk(op_denoised, aatype='Eedi3', opencl=True)
op_aa_b = lvf.fix_eedi3(op_denoised)
op_aa = fvf.rfs(op_aa_a, op_aa_b, mappings="[1276 1305]")

op_deband_low = core.f3kdb.Deband(op_aa, range=16, y=48, cr=40, cb=40, grainy=12, grainc=0, output_depth=16)
op_deband_high = core.f3kdb.Deband(op_aa, range=18, y=64, cr=56, cb=56, grainy=18, grainc=0, output_depth=16)
op_deband_higher = core.f3kdb.Deband(op_aa, range=19, y=64, cr=56, cb=56, grainy=24, grainc=0, output_depth=16)
op_deband_very_high = core.f3kdb.Deband(op_aa, range=7, y=200, cr=192, cb=192, grainy=0, grainc=0, output_depth=16) 
# Don't ever do this unless you *HAVE* to, please - https://slowpics.org/comparison/21b25059-693c-4e2c-8510-e5f141c1faa6
op_deband_very_high = core.f3kdb.Deband(op_deband_very_high, range=21, y=72, cr=64, cb=64, grainy=24, grainc=0, output_depth=16)
op_deband = fvf.rfs(op_deband_low, op_aa, mappings="[0 313] [1976 2159]")
op_deband = fvf.rfs(op_deband, op_deband_high, mappings="[1245 1251]")
op_deband = fvf.rfs(op_deband, op_deband_higher, mappings="[1078 1128]")
op_deband = fvf.rfs(op_deband, op_deband_very_high, mappings="[1227 1244]")

op_mask_a = kgf.retinex_edgemask(op_aa, sigma=1).resize.Spline36(format=vs.GRAY16)
op_mask_b = core.std.Prewitt(op_aa, scale=4, planes=0).std.Deflate().std.Binarize(4700, planes=0).resize.Spline36(format=vs.GRAY16) 
# Tried catching the bright lineart in her hair, but it didn't work. This catches less random artifacts on that particular scene, so keeping it.
op_mask = fvf.rfs(op_mask_a, op_mask_b, mappings="[1129 1204]")
op_maskmerged = core.std.MaskedMerge(op_deband, op_aa, op_mask)

op_merge = fvf.rfs(op_maskmerged, src_op, mappings="[971 1076]")

op_grain = kgf.adaptive_grain(op_merge, 0.5)

out = op_grain
final = fvf.Depth(out, 10)
final.set_output()