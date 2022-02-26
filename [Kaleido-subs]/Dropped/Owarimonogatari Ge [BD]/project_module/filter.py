from functools import partial
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Union

import vapoursynth as vs
from lvsfunc.types import Range
from vsutil import Range as ColourRange
from vsutil import (depth, get_depth, get_w, get_y, iterate, join, plane,
                    scale_value)

from .util import _get_bits

core = vs.core


def detail_mask(clip: vs.VideoNode,
                sigma: float = 1.0, rxsigma: List[int] = [50, 200, 350],
                pf_sigma: Optional[float] = 1.0,
                rad: int = 3, brz: Tuple[int, int] = (2500, 4500),
                rg_mode: int = 17,
                ) -> vs.VideoNode:
    """
    A detail mask aimed at preserving as much detail as possible within darker areas,
    even if it contains mostly noise.
    """
    import jvsfunc as jvf
    bits, clip = _get_bits(clip)

    clip_y = get_y(clip)
    pf = core.bilateral.Gaussian(clip_y, sigma=pf_sigma) if pf_sigma else clip_y
    ret = core.retinex.MSRCP(pf, sigma=rxsigma, upper_thr=0.005)

    blur_ret = core.bilateral.Gaussian(ret, sigma=sigma)
    blur_ret_diff = core.std.Expr([blur_ret, ret], "x y -")
    blur_ret_dfl = core.std.Deflate(blur_ret_diff)
    blur_ret_ifl = iterate(blur_ret_dfl, core.std.Inflate, 4)
    blur_ret_brz = core.std.Binarize(blur_ret_ifl, brz[0])
    blur_ret_brz = jvf.expr_close(blur_ret_brz, size=8)

    prewitt_mask = core.std.Prewitt(clip_y).std.Binarize(brz[1])
    prewitt_ifl = prewitt_mask.std.Deflate().std.Inflate()
    prewitt_brz = core.std.Binarize(prewitt_ifl, brz[1])
    prewitt_brz = jvf.expr_close(prewitt_brz, size=8)

    merged = core.std.Expr([blur_ret_brz, prewitt_brz], "x y +")
    rm_grain = core.rgvs.RemoveGrain(merged, rg_mode)
    return rm_grain if bits == 16 else depth(rm_grain, bits)


def rescaler(clip: vs.VideoNode, height: int, shader_file: str, mask_thr: float = 0.055,
             blurry_scale_ranges: Iterable[Range] = []) -> Tuple[vs.VideoNode, vs.VideoNode]:
    """
    Rescaling function. Combines multiple descales + downscales into one image,
    and then upscales using a mix of FSRCNNX, a dehalo'd clip, and nnedi3.
    This is then merged with an edgemask to the original clip's luma.

    :param clip:                    Input clip
    :param height:                  Descale height. Width is auto-calculated
    :param shader_file:             FSRCNNX (or if you really insist, other scaler) hook file
    :param mask_thr:                Descale detail mask threshold
    :param blurry_scale_ranges:     Ranges for a regular nnedi3 reupscale as opposed to this mixed nonsense

    :return:                        Rescaled clip and descale detail maks
    """
    import lvsfunc as lvf
    import vardefunc as vdf
    from muvsfunc import SSIM_downsample
    from vardefunc.mask import FDOG

    bits, clip = _get_bits(clip, expected_depth=32)

    clip_y = get_y(clip)

    scalers: List[Callable[[vs.VideoNode, int, int], vs.VideoNode]] = [
        lvf.kernels.Catrom().descale,
        lvf.kernels.Bilinear().descale,
        lvf.kernels.BicubicSharp().descale,
        lvf.kernels.Spline36().descale,
        lvf.kernels.Catrom().scale
    ]

    descale_clips = [scaler(clip_y, get_w(height, clip.width/clip.height), height) for scaler in scalers]

    descale_clip = core.std.Expr(descale_clips, 'x y z a min max min y z a max min max z a min max')
    rescaled_fsrcnnx = vdf.scale.fsrcnnx_upscale(descale_clip, clip.width, clip.height, shader_file)
    dehalo_fsrcnnx = depth(lvf.dehalo.masked_dha(depth(rescaled_fsrcnnx, 16), rx=1.6, ry=1.4, brightstr=0.5), 32)
    supersample = vdf.scale.nnedi3_upscale(descale_clip, use_znedi=False, pscrn=1)
    rescaled_nn3 = SSIM_downsample(supersample, clip.width, clip.height, smooth=((3 ** 2 - 1) / 12) ** 0.5,
                                   sigmoid=True, filter_param_a=0, filter_param_b=0)
    rescaled_fsrcmix = core.std.Expr([rescaled_fsrcnnx, rescaled_nn3, dehalo_fsrcnnx], "x y min z min")
    rescale = lvf.rfs(rescaled_fsrcmix, rescaled_nn3, blurry_scale_ranges)

    l_mask = FDOG().get_mask(clip_y, lthr=0.065, hthr=0.065).std.Maximum().std.Minimum()
    l_mask = l_mask.std.Median().std.Convolution([1] * 9)  # stolen from varde xd
    masked_rescale = core.std.MaskedMerge(clip_y, rescale, l_mask)

    scaled = vdf.misc.merge_chroma(masked_rescale, clip)

    upscale = lvf.kernels.Catrom().scale(descale_clip, 1920, 1080)
    detail_mask = lvf.scale.descale_detail_mask(clip_y, upscale, threshold=mask_thr)

    scaled_down = scaled if bits == 32 else depth(scaled, bits)
    mask_down = detail_mask if bits == 32 else \
        depth(detail_mask, 16, range_in=ColourRange.FULL, range=ColourRange.LIMITED)

    return scaled_down, mask_down


def masked_f3kdb(clip: vs.VideoNode,
                 rad: int = 16,
                 thr: Union[int, List[int]] = 24,
                 grain: Union[int, List[int]] = [12, 0],
                 mask_args: Dict[str, Any] = {}
                 ) -> vs.VideoNode:
    """Basic f3kdb debanding with detail mask"""
    from debandshit import dumb3kdb

    deb_mask_args: Dict[str, Any] = dict(brz=(scale_value(1000, 16, 32), scale_value(2750, 16, 32)))
    deb_mask_args |= mask_args

    bits, clip = _get_bits(clip)

    deband_mask = detail_mask(clip, **deb_mask_args)

    deband = dumb3kdb(clip, radius=rad, threshold=thr, grain=grain, seed=69420)
    deband_masked = core.std.MaskedMerge(deband, clip, deband_mask)
    deband_masked = deband_masked if bits == 16 else depth(deband_masked, bits)
    return deband_masked


def masked_placebo(clip: vs.VideoNode,
                   rad: int = 12, thr: Union[int, List[int]] = 4,
                   itr: int = 2, grain: int = 2,
                   mask_args: Dict[str, Any] = {}
                   ) -> vs.VideoNode:
    """Basic placebo debanding with detail mask"""
    deb_mask_args: Dict[str, Any] = dict(brz=(scale_value(1750, 16, 32), scale_value(4000, 16, 32)))
    deb_mask_args |= mask_args

    bits, clip = _get_bits(clip)

    deband_mask = detail_mask(clip, **deb_mask_args)

    deband = placebo_debander(clip, radius=rad, threshold=thr, grain=grain, iterations=itr)
    deband_masked = core.std.MaskedMerge(deband, clip, deband_mask)
    deband_masked = deband_masked if bits == 16 else depth(deband_masked, bits)
    return deband_masked


def placebo_debander(clip: vs.VideoNode, grain: int = 4, **deband_args: Any) -> vs.VideoNode:
    return join([  # Still not sure why splitting it up into planes is faster, but hey! It works!
        core.placebo.Deband(plane(clip, 0), grain=grain, **deband_args),
        core.placebo.Deband(plane(clip, 1), grain=0, **deband_args),
        core.placebo.Deband(plane(clip, 2), grain=0, **deband_args)
    ])


def line_darkening(clip: vs.VideoNode, strength: float = 0.2, **kwargs: Any) -> vs.VideoNode:
    """
    Darken lineart through Toon.
    Taken from varde's repository.
    """
    from havsfunc import Toon

    darken = Toon(clip, strength, **kwargs)
    darken_mask = core.std.Expr(
        [core.std.Convolution(clip, [5, 10, 5, 0, 0, 0, -5, -10, -5], divisor=4, saturate=False),
         core.std.Convolution(clip, [5, 0, -5, 10, 0, -10, 5, 0, -5], divisor=4, saturate=False)],
        ['x y max {neutral} / 0.86 pow {peak} *'
            .format(neutral=1 << (clip.format.bits_per_sample-1),  # type: ignore[union-attr]
                    peak=(1 << clip.format.bits_per_sample)-1)])  # type: ignore[union-attr]
    return core.std.MaskedMerge(clip, darken, darken_mask)


def auto_lbox(clip: vs.VideoNode, flt: vs.VideoNode, flt_lbox: vs.VideoNode,
              crop_top: int = 130, crop_bottom: int = 130) -> vs.VideoNode:
    """
    Automatically determining what scenes have letterboxing
    and applying the correct edgefixing to it
    """
    from lvsfunc.misc import get_prop

    def _letterboxed(n: int, f: vs.VideoFrame,
                     clip: vs.VideoNode, flt: vs.VideoNode, flt_lbox: vs.VideoNode
                     ) -> vs.VideoNode:
        crop = clip.std.CropRel(top=crop_top, bottom=crop_bottom) \
            .std.AddBorders(top=crop_top, bottom=crop_bottom,
                            color=[luma_val, chr_val, chr_val])

        clip_prop = round(get_prop(clip.std.PlaneStats().get_frame(n), "PlaneStatsAverage", float), 4)
        crop_prop = round(get_prop(crop.std.PlaneStats().get_frame(n), "PlaneStatsAverage", float), 4)

        if crop_prop == clip_prop:
            return flt_lbox.std.SetFrameProp("Letterbox", intval=1)
        return flt.std.SetFrameProp("Letterbox", intval=0)

    luma_val = scale_value(16, 8, get_depth(clip))
    chr_val = scale_value(128, 8, get_depth(clip))

    return core.std.FrameEval(clip, partial(_letterboxed, clip=clip, flt=flt, flt_lbox=flt_lbox), clip)


def transpose_sraa(clip: vs.VideoNode, **kwargs: Any) -> vs.VideoNode:
    import lvsfunc as lvf

    aa = lvf.sraa(clip.std.Transpose(), **kwargs)
    return lvf.sraa(aa.std.Transpose(), **kwargs)
