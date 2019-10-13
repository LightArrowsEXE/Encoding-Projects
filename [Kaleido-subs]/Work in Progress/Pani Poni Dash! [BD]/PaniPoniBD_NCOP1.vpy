import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import mvsfunc as mvf
import havsfunc as haf
from vsutil import *
core = vs.core


def main(src, height=720, aatype='Eedi3', mappings=None, return_crop=False):
    def crop_n_edgefix(src):
        src = core.std.CropRel(src, 20, 18, 8, 6)
        return core.edgefixer.ContinuityFixer(src, [2,1,1], [2,1,1], [2,1,1], [2,1,1])

    def scaling(src, height):
        scaled = core.resize.Bicubic(src, get_w(height), height, format=vs.YUV444P16)
        y, u, v = kgf.split(scaled)
        y = haf.HQDeringmod(y, mrad=10, msmooth=1, nrmode=2, darkthr=4, sharp=0, mthr=56)
        uv = [u, v]
        u = core.resize.Point(uv[0], src_left=-0.25, src_top=0.25)
        v = core.resize.Point(uv[1], src_left=0.25, src_top=-0.25)
        u, v = [haf.HQDeringmod(plane, mrad=4, msmooth=1, nrmode=2, darkthr=12, sharp=0, mthr=56) for plane in uv]
        merge = kgf.join([y, u, v])
        return merge, scaled

    def lines(src, ref, aatype):
        l_mask_a = kgf.retinex_edgemask(ref)
        aa = lvf.nneedi3_clamp(src, mask=l_mask_a, strength=1.2)
        return haf.LSFmod(aa, strength=120, soft=20, edgemode=1, Smethod=2, Lmode=2, defaults="slow")

    crop = crop_n_edgefix(src)
    crop = fvf.Depth(crop, 32)
    if return_crop:
        return crop
    merge, scaled = scaling(crop, height)

    d_mask = kgf.adaptive_grain(scaled, show_mask=True, luma_scaling=2)
    aa = lines(merge, scaled, aatype)
    return core.std.MaskedMerge(aa, merge, d_mask)


def end(src, ref, height, times):
    def crop_card(src):
        crop = core.std.Crop(src, 160, 160, 96, 94)
        return crop

    def scaling(src, height):
        return core.resize.Bicubic(src, get_w(height), height, format=vs.YUV444P16)

    crop = crop_card(src)
    scaled = scaling(crop, height)
    scaled = core.std.AssumeFPS(scaled, ref)
    return core.std.Loop(scaled, times)


src = lvf.src(r"BDMV/[BDMV][Pani Poni Dash][ぱにぽにだっしゅ！][BD BOX]/DISC6/BDMV/STREAM/00007.m2ts")
src = src[24:2183]
t = src
src = core.std.Levels(src, min_in=0, max_in=255, min_out=16, max_out=235, planes=0)


filtered = main(src, 576)

d_mask = kgf.adaptive_grain(filtered, show_mask=True, luma_scaling=4)
denoise_a = mvf.BM3D(filtered, sigma=[2,1], matrix=1)
deband_a = core.f3kdb.Deband(denoise_a, range=13, y=32, cb=24, cr=24, grainy=24, grainc=0, output_depth=16)
denoise_b = mvf.BM3D(filtered, sigma=[1,0.5], matrix=1)
deband_b = core.f3kdb.Deband(denoise_b, range=13, y=32, cb=24, cr=24, grainy=24, grainc=0, output_depth=16)
deband = core.std.MaskedMerge(deband_a, deband_b, d_mask)

grain = kgf.adaptive_grain(deband, 0.4)


out = grain
final = fvf.Depth(out, 10)
t = main(t, return_crop=True).resize.Spline36(filtered.width, filtered.height, format=filtered.format)
comp = lvf.comp(t, out, None, True, None, True)
final.set_output()