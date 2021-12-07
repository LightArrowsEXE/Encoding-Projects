from typing import Any, Dict, List, Optional, Tuple, Union

import vapoursynth as vs
from lvsfunc.kernels import Catrom, Kernel
from vsutil import depth, get_w, get_y, iterate, join, plane

from .util import _get_bits

core = vs.core


def detail_mask(clip: vs.VideoNode,
                sigma: float = 1.0, rxsigma: List[int] = [50, 200, 350],
                pf_sigma: Optional[float] = 1.0, brz: Tuple[int, int] = (2500, 4500),
                rg_mode: int = 17) -> vs.VideoNode:
    """
    A detail mask aimed at preserving as much detail as possible within darker areas,
    even if it contains mostly noise.
    """
    bits, clip = _get_bits(clip)

    clip_y = get_y(clip)
    pf = core.bilateral.Gaussian(clip_y, sigma=pf_sigma) if pf_sigma else clip_y
    ret = core.retinex.MSRCP(pf, sigma=rxsigma, upper_thr=0.005)

    blur_ret = core.bilateral.Gaussian(ret, sigma=sigma)
    blur_ret_diff = core.std.Expr([blur_ret, ret], "x y -")
    blur_ret_dfl = core.std.Deflate(blur_ret_diff)
    blur_ret_ifl = iterate(blur_ret_dfl, core.std.Inflate, 4)
    blur_ret_brz = core.std.Binarize(blur_ret_ifl, brz[0])
    blur_ret_brz = core.morpho.Close(blur_ret_brz, size=8)

    prewitt_mask = core.std.Prewitt(clip_y).std.Binarize(brz[1])
    prewitt_ifl = prewitt_mask.std.Deflate().std.Inflate()
    prewitt_brz = core.std.Binarize(prewitt_ifl, brz[1])
    prewitt_brz = core.morpho.Close(prewitt_brz, size=4)

    merged = core.std.Expr([blur_ret_brz, prewitt_brz], "x y +")
    rm_grain = core.rgvs.RemoveGrain(merged, rg_mode)
    return rm_grain if bits == 16 else depth(rm_grain, bits)


def placebo_debander(clip: vs.VideoNode, grain: int = 4, **deband_args: Any) -> vs.VideoNode:
    return join([  # Still not sure why splitting it up into planes is faster, but hey!
        core.placebo.Deband(plane(clip, 0), grain=grain, **deband_args),
        core.placebo.Deband(plane(clip, 1), grain=0, **deband_args),
        core.placebo.Deband(plane(clip, 2), grain=0, **deband_args)
    ])


def line_darkening(clip: vs.VideoNode, strength: float = 0.2, **kwargs: Any) -> vs.VideoNode:
    """
    Darken lineart through Toon.
    Taken from varde's repository.
    """
    import havsfunc as haf

    darken = haf.Toon(clip, strength, **kwargs)
    darken_mask = core.std.Expr(
        [core.std.Convolution(clip, [5, 10, 5, 0, 0, 0, -5, -10, -5], divisor=4, saturate=False),
         core.std.Convolution(clip, [5, 0, -5, 10, 0, -10, 5, 0, -5], divisor=4, saturate=False)],
        ['x y max {neutral} / 0.86 pow {peak} *'
            .format(neutral=1 << (clip.format.bits_per_sample-1),  # type: ignore[union-attr]
                    peak=(1 << clip.format.bits_per_sample)-1)])  # type: ignore[union-attr]
    return core.std.MaskedMerge(clip, darken, darken_mask)


def transpose_sraa(clip: vs.VideoNode, **kwargs: Any) -> vs.VideoNode:
    from lvsfunc import sraa

    aa = sraa(clip.std.Transpose(), **kwargs)
    return sraa(aa.std.Transpose(), **kwargs)


def masked_f3kdb(clip: vs.VideoNode,
                 rad: int = 16,
                 thr: Union[int, List[int]] = 24,
                 grain: Union[int, List[int]] = [12, 0],
                 mask_args: Dict[str, Any] = {}
                 ) -> vs.VideoNode:
    """Basic f3kdb debanding with detail mask"""
    from debandshit import dumb3kdb

    deb_mask_args: Dict[str, Any] = dict(brz=(1000, 2750))
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
    deb_mask_args: Dict[str, Any] = dict(brz=(1750, 4000))
    deb_mask_args |= mask_args

    bits, clip = _get_bits(clip)

    deband_mask = detail_mask(clip, **deb_mask_args)

    deband = placebo_debander(clip, radius=rad, threshold=thr, grain=grain, iterations=itr)
    deband_masked = core.std.MaskedMerge(deband, clip, deband_mask)
    deband_masked = deband_masked if bits == 16 else depth(deband_masked, bits)
    return deband_masked


def auto_descale(clip: vs.VideoNode, height: int = 720, thr: float = 0.000015) -> vs.VideoNode:
    """
    Quick wrapper to descale to Sharp Bicubic and Spline36,
    compare them, and then pick one or the other.

    Could've sworn there was another function that did this, but I forgot what it was lol
    """
    from functools import partial

    from lvsfunc.kernels import BicubicSharp, Spline36
    from lvsfunc.util import get_prop

    def _compare(n: int, f: vs.VideoFrame,
                 sharp: vs.VideoNode,
                 spline: vs.VideoNode) -> vs.VideoNode:
        """Compare PlaneStatsDiff's"""
        sharp_diff = get_prop(f[0], 'PlaneStatsDiff', float)
        spline_diff = get_prop(f[1], 'PlaneStatsDiff', float)

        return sharp if spline_diff - thr > sharp_diff else spline

    clip_y = get_y(clip)
    sharp = BicubicSharp().descale(clip_y, get_w(height, clip.width/clip.height), height)
    sharp_up = BicubicSharp().scale(sharp, clip.width, clip.height)

    spline = Spline36().descale(clip_y, get_w(height, clip.width/clip.height), height)
    spline_up = Spline36().scale(spline, clip.width, clip.height)

    # We need a diff between the rescaled clips and the original clip
    sharp_diff = sharp_up.std.PlaneStats(clip_y)
    spline_diff = spline_up.std.PlaneStats(clip_y)

    # Extra props for future frame evalling in case it might prove useful (for credits, for example)
    sharp = sharp.std.SetFrameProp('scaler', data='BicubicSharp')
    spline = spline.std.SetFrameProp('scaler', data='Spline36')

    return core.std.FrameEval(sharp, partial(_compare, sharp=sharp, spline=spline), [sharp_diff, spline_diff])


def descale_fields(clip: vs.VideoNode, height: int = 720,
                   tff: bool = True, kernel: Kernel = Catrom,
                   shift: Tuple[float, float] = [0.0, 0.0]) -> vs.VideoNode:
    """
    Simple descaling wrapper for interwoven upscaled fields

    :param clip:        Input clip
    :param height:      Native height. Will be divided by two internally.
                        Width is autocalculated using height and the clip's aspect ratio.
    :param tff:         Top-field-first
    :param kernel:      lvsfunc.Kernel object
    :param shift:       [src_top, src_left]

    :return:            Descaled GRAY clip
    """
    height_field = height/2

    clip = clip.std.SetFieldBased(2-int(tff))

    sep = core.std.SeparateFields(get_y(clip))
    descaled = kernel().descale(sep, get_w(height, clip.width/clip.height), height_field, shift)
    weave_y = core.std.DoubleWeave(descaled)[::2].std.SetFrameProp('scaler', data=f'{kernel.__name__} (Fields)')
    return weave_y.std.SetFrameProp('_FieldBased', intval=0)
