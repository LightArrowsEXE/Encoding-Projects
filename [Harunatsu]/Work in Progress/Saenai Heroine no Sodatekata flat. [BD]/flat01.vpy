import vapoursynth as vs
import kagefunc as kgf
import vsTAAmbk as taa
import lvsfunc as lvf
import fvsfunc as fvf
import havsfunc as haf
core = vs.core

opstart = 3453
opend = 5611
edstart = 30283
edend = 32443

src = lvf.src(r"[BDMV]冴えない彼女の育てかた♭Vol.01~Vol.06/[BDMV]冴えない彼女の育てかた♭ VOL.01/BDMV/STREAM/00002.m2ts")
src = src[:32847]
src = fvf.Depth(src, 16)

src_op = lvf.src(r"[BDMV]冴えない彼女の育てかた♭Vol.01~Vol.06/[BDMV]冴えない彼女の育てかた♭ VOL.01/BDMV/STREAM/00009.m2ts")
src_op = src_op[24:2184]
src_op = fvf.Depth(src_op, 16)

src_ed = lvf.src(r"[BDMV]冴えない彼女の育てかた♭Vol.01~Vol.06/[BDMV]冴えない彼女の育てかた♭ VOL.01/BDMV/STREAM/00010.m2ts")
src_ed = src_ed[24:2184]
src_ed = fvf.Depth(src_ed, 16)

blank = core.std.BlankClip(src)
blank = blank[0]

# # # # # # # # OP filtering # # # # # # # #

op_denoised = lvf.qden(src_op, h=0.4)
op_denoised = haf.ContraSharpening(op_denoised, src_op)

op_aa_a = taa.TAAmbk(op_denoised, aatype='Eedi3', opencl=True)
op_aa_b = lvf.NnEedi3(op_denoised)
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

op_out = blank*opstart+op_grain
op_out = op_out[opstart:opend]

# # # # # # # # OP filtering # # # # # # # #
# # # # # # # # ED filtering # # # # # # # #

ed_denoised = lvf.denoise(src_ed, h=0.4)
ed_denoised = haf.ContraSharpening(ed_denoised, src_ed)

ed_aa = taa.TAAmbk(ed_denoised, aatype='Eedi3', opencl=True)
ed_deband = core.f3kdb.Deband(ed_aa, range=16, y=48, cr=40, cb=40, grainy=0, grainc=0, output_depth=16)

ed_grain = kgf.adaptive_grain(ed_deband, 0.5)

ed_out = blank*edstart+ed_grain
ed_out = ed_out[edstart:edend]

# # # # # # # # ED filtering # # # # # # # #

# fix for an animation error. Never again, please.
bookmask1 = core.resize.Spline36(core.imwri.Read(r"flat01-book1.png"), format=vs.YUV420P16, matrix_s='709')
bookmask2 = core.resize.Spline36(core.imwri.Read(r"flat01-book2.png"), format=vs.YUV420P16, matrix_s='709')
bookmask3 = core.resize.Spline36(core.imwri.Read(r"flat01-book3.png"), format=vs.YUV420P16, matrix_s='709')
bookmask4 = core.resize.Spline36(core.imwri.Read(r"flat01-book4.png"), format=vs.YUV420P16, matrix_s='709')
bookmask5 = core.resize.Spline36(core.imwri.Read(r"flat01-book5.png"), format=vs.YUV420P16, matrix_s='709')*10600
fix = kgf.insert_clip(src, bookmask1, 10509) 
fix = kgf.insert_clip(fix, bookmask1, 10510)
fix = kgf.insert_clip(fix, bookmask1, 10511)
fix = kgf.insert_clip(fix, bookmask2, 10512)
fix = kgf.insert_clip(fix, bookmask2, 10513)
fix = kgf.insert_clip(fix, bookmask2, 10514)
fix = kgf.insert_clip(fix, bookmask3, 10515)
fix = kgf.insert_clip(fix, bookmask3, 10516)
fix = kgf.insert_clip(fix, bookmask3, 10517)
fix = kgf.insert_clip(fix, bookmask4, 10518)
fix = kgf.insert_clip(fix, bookmask4, 10519)
fix = kgf.insert_clip(fix, bookmask4, 10520)
fix = kgf.insert_clip(fix, bookmask5[10521:10569], 10521)

denoised = lvf.qden(fix, h=0.4)
denoised = haf.ContraSharpening(denoised, fix)

aa_a = taa.TAAmbk(denoised, aatype='Eedi3', opencl=True)
aa_b = taa.TAAmbk(denoised, aatype='Eedi3', opencl=True, cycle=2)
aa = fvf.rfs(aa_a, aa_b, mappings="[5611 5736]")

deband = core.f3kdb.Deband(aa, range=16, y=48, cr=40, cb=40, grainy=12, grainc=0, output_depth=16)

mask = kgf.retinex_edgemask(fix, sigma=1)
masked = core.std.MaskedMerge(deband, aa, mask)

grain = kgf.adaptive_grain(masked, 0.1)

out = grain
out = kgf.insert_clip(out, op_out, opstart)
out = kgf.insert_clip(out, ed_out, edstart)

final = fvf.Depth(out, 10)
final.set_output()