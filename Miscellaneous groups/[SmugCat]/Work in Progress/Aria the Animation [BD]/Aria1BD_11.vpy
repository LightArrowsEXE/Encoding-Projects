import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import vsTAAmbk as taa
import havsfunc as haf
core = vs.core


src = lvf.src(r"BDMV/ARIA SEASON ONE BD/ARIAS1BD3/BDMV/STREAM/00001.m2ts")
src = src[30:43831]
src = core.std.CropRel(src, left=248, right=248, top=8, bottom=6)
src = core.edgefixer.ContinuityFixer(src, left=[2,1,1], top=[2,1,1], right=[2,1,1], bottom=1)
src = fvf.Depth(src, 16)


scaled = core.resize.Spline36(src, 640, 480, format=vs.YUV444P16)

dehalo = haf.HQDeringmod(scaled, nrmode=2, darkthr=0, sharp=0, mthr=56)
darken = haf.FastLineDarkenMOD(dehalo, strength=28, protection=3, luma_cap=191, threshold=2, thinning=0)
aa = taa.TAAmbk(dehalo, aatype='Eedi3')

dark_mask = kgf.adaptive_grain(scaled, show_mask=True, luma_scaling=12).std.Binarize()
blur = core.std.BoxBlur(scaled) # blur away the noise for more accurate edgemask
lineart_mask = kgf.retinex_edgemask(blur, 1).std.Maximum().std.Binarize()
deband_mask = core.std.Expr([dark_mask, lineart_mask], expr='x y -', format=vs.GRAY)

deband_a = core.f3kdb.Deband(aa, range=8, y=24, cb=16, cr=16, grainy=0, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(aa, range=11, y=32, cb=24, cr=24, grainy=0, grainc=0, output_depth=16)
deband = core.std.MaskedMerge(deband_a, deband_b, deband_mask)
grain = kgf.adaptive_grain(deband, 0.1)


out = grain
final = fvf.Depth(out, 10)
final.set_output()
