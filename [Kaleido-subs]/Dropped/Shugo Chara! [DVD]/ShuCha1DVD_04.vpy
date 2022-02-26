import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import vsTAAmbk as taa
import havsfunc as haf
import mvsfunc as mvf
import functools
core = vs.core


def postprocess(n, f, clip, deinterlaced):
   if f.props['_Combed'] > 0:
      return deinterlaced
   else:
      return clip


def decimate(src):
    src = core.vivtc.VFM(src, 1)
    return core.vivtc.VDecimate(src)


def detelecine(src):
    matched = core.vivtc.VFM(src, 1)
    src = core.nnedi3.nnedi3(src, field=1)
    return core.std.FrameEval(matched, functools.partial(postprocess, clip=matched, deinterlaced=src), prop_src=matched)


src = lvf.src(r"DVDISO/[DVDISO][アニメ][SHUGO CHARA!][Vol.1-16 Fin]/SHUGO_CHARA_02.d2v")
src = decimate(src)
src = detelecine(src)
src = core.std.CropRel(src, 2, 2, 2, 0)
src = core.edgefixer.ContinuityFixer(src, left=[4,2,2], top=[2,1,1], right=[4,2,2], bottom=[0,0,0])
src = fvf.Depth(src, 16)
src = src[1721:36726]

scaled = core.resize.Spline36(src, 848, 480)


denoise_mask = kgf.adaptive_grain(scaled, show_mask=True, luma_scaling=4)
denoise_a = core.w2xc.Waifu2x(fvf.Depth(scaled, 32), noise=1, scale=1)
denoise_a = fvf.Depth(denoise_a, 16)
denoise_b = mvf.BM3D(scaled, sigma=[3,1.5])
denoise = core.std.MaskedMerge(denoise_a, denoise_b, denoise_mask)

sharpen = haf.LSFmod(denoise, strength=120, soft=10, edgemode=1, Smethod=2, Lmode=2)
dehalo = haf.HQDeringmod(sharpen, darkthr=0, sharp=0, mthr=56)
darken = haf.FastLineDarkenMOD(dehalo, strength=36, protection=3, luma_cap=191, threshold=2, thinning=0)
aa = taa.TAAmbk(darken, aatype='Nnedi3', cycle=1)

dark_mask = kgf.adaptive_grain(scaled, show_mask=True, luma_scaling=12).std.Binarize()
blur = core.std.BoxBlur(scaled) # blur away the noise for more accurate edgemask
lineart_mask = kgf.retinex_edgemask(blur, 1).std.Maximum().std.Binarize()
deband_mask = core.std.Expr([dark_mask, lineart_mask], expr='x y -', format=vs.GRAY)
deband_a = core.f3kdb.Deband(aa, range=10, y=24, cb=16, cr=16, grainy=12, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(aa, range=15, y=40, cb=32, cr=32, grainy=24, grainc=0, output_depth=16)
deband = core.std.MaskedMerge(deband_a, deband_b, deband_mask)
grain = kgf.adaptive_grain(deband, 0.6, luma_scaling=4)


out = grain
final = fvf.Depth(out, 10)
final.set_output()