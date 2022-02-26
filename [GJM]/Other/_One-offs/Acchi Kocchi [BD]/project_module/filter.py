from typing import Any, Callable, Dict, List, Tuple, Union

import vapoursynth as vs
from vsutil import depth, join, plane

from .util import _get_bits

core = vs.core


def detail_mask(clip: vs.VideoNode, sigma: float = 1.0,
                detail_brz: int = 2500, lines_brz: int = 4500,
                blur_func: Callable[[vs.VideoNode, vs.VideoNode, float],
                                    vs.VideoNode] = core.bilateral.Bilateral,  # type: ignore
                edgemask_func: Callable[[vs.VideoNode], vs.VideoNode] = core.std.Prewitt,
                rg_mode: int = 17) -> vs.VideoNode:
    """
    A detail mask aimed at preserving as much detail as possible within darker areas,
    even if it winds up being mostly noise.
    Currently still in the beta stage.
    Please report any problems or feedback in the IEW Discord (link in the README).
    :param clip:            Input clip
    :param sigma:           Sigma for the detail mask.
                            Higher means more detail and noise will be caught.
    :param detail_brz:      Binarizing for the detail mask.
                            Default values assume a 16bit clip, so you may need to adjust it yourself.
                            Will not binarize if set to 0.
    :param lines_brz:       Binarizing for the prewitt mask.
                            Default values assume a 16bit clip, so you may need to adjust it yourself.
                            Will not binarize if set to 0.
    :param blur_func:       Blurring function used for the detail detection.
                            Must accept the following parameters: ``clip``, ``ref_clip``, ``sigma``.
    :param edgemask_func:   Edgemasking function used for the edge detection
    :param rg_mode:         Removegrain mode performed on the final output
    """
    import lvsfunc as lvf
    from vsutil import get_y, iterate

    if clip.format is None:
        raise ValueError("detail_mask: 'Variable-format clips not supported'")

    clip_y = get_y(clip)
    blur_pf = core.bilateral.Gaussian(clip_y, sigma=sigma / 4 * 3)

    blur_pref = blur_func(clip_y, blur_pf, sigma)
    blur_pref_diff = core.std.Expr([blur_pref, clip_y], "x y -").std.Deflate()
    blur_pref = iterate(blur_pref_diff, core.std.Inflate, 4)

    prew_mask = edgemask_func(clip_y).std.Deflate().std.Inflate()

    if detail_brz > 0:
        blur_pref = blur_pref.std.Binarize(detail_brz)
    if lines_brz > 0:
        prew_mask = prew_mask.std.Binarize(lines_brz)

    merged = core.std.Expr([blur_pref, prew_mask], "x y +")
    rm_grain = lvf.util.pick_removegrain(merged)(merged, rg_mode)

    return depth(rm_grain, clip.format.bits_per_sample)


def linemask(clip: vs.VideoNode, strength: int = 200,
             protection: int = 2, luma_cap: int = 224,
             threshold: float = 3) -> Tuple[vs.VideoNode, vs.VideoNode]:
    """
    Lineart mask from havsfunc.FastLineDarkenMod, using the very same syntax.

    Furthermore, it checks the overall planestatsaverage of the frame
    to determine if it's a super grainy scene or not.
    """
    import math
    from functools import partial
    from typing import List

    from lvsfunc.misc import get_prop
    from vsutil import depth, get_depth, get_y

    def _reduce_grain(n: int, f: vs.VideoFrame, clips: List[vs.VideoNode]) -> vs.VideoNode:
        return clips[1] if get_prop(f, 'PlaneStatsAverage', float) > 0.032 else clips[0]

    def _cround(x: float) -> float:
        return math.floor(x + 0.5) if x > 0 else math.ceil(x - 0.5)

    assert clip.format

    clip_y = get_y(depth(clip, 8))
    bits = clip.format.bits_per_sample

    peak = (1 << get_depth(clip_y)) - 1

    strngth = strength / 128
    lum = _cround(luma_cap * peak / 255) if peak != 1 else luma_cap / 255
    thr = _cround(threshold * peak / 255) if peak != 1 else threshold / 255

    maxed = clip_y.std.Maximum(threshold=peak / (protection + 1)).std.Minimum()
    dark = core.std.Expr([clip_y, maxed],
                         expr=f'y {lum} < y {lum} ? x {thr} + > x y {lum} < y {lum} ? - 0 ? {strngth} * x +')
    extr = core.std.Lut2(clip_y, dark, function=lambda x, y: 255 if abs(x - y) else 0)

    dedot = extr.rgvs.RemoveGrain(6)
    blur = dedot.std.Convolution(matrix=[1, 2, 1, 2, 0, 2, 1, 2, 1])
    degrain = core.std.FrameEval(dedot, partial(_reduce_grain, clips=[dedot, blur]), dedot.std.PlaneStats())

    return dark, depth(degrain, bits)


def masked_f3kdb(clip: vs.VideoNode,
                 rad: int = 16,
                 thr: Union[int, List[int]] = 24,
                 grain: Union[int, List[int]] = [12, 0],
                 mask_args: Dict[str, Any] = {}
                 ) -> vs.VideoNode:
    """Basic f3kdb debanding with detail mask """
    from debandshit import dumb3kdb

    deb_mask_args: Dict[str, Any] = dict(detail_brz=1500, lines_brz=1000)
    deb_mask_args |= mask_args

    bits, clip = _get_bits(clip)

    deband_mask = detail_mask(clip, **deb_mask_args)

    deband = dumb3kdb(clip, radius=rad, threshold=thr, grain=grain)
    deband_masked = core.std.MaskedMerge(deband, clip, deband_mask)
    deband_masked = deband_masked if bits == 16 else depth(deband_masked, bits)
    return deband_masked


def placebo_debander(clip: vs.VideoNode, grain: int = 4, **deband_args: Any) -> vs.VideoNode:
    return join([  # Still not sure why splitting it up into planes is faster, but hey!
        core.placebo.Deband(plane(clip, 0), grain=grain, **deband_args),
        core.placebo.Deband(plane(clip, 1), grain=0, **deband_args),
        core.placebo.Deband(plane(clip, 2), grain=0, **deband_args)
    ])


def masked_placebo(clip: vs.VideoNode,
                   rad: int = 12, thr: Union[int, List[int]] = 4,
                   itr: int = 2, grain: int = 2,
                   mask_args: Dict[str, Any] = {},
                   show_mask: bool = False) -> vs.VideoNode:
    """Basic placebo debanding with detail mask"""
    deb_mask_args: Dict[str, Any] = dict(detail_brz=1750, lines_brz=4000)
    deb_mask_args |= mask_args

    bits, clip = _get_bits(clip)

    deband_mask = detail_mask(clip, **deb_mask_args)

    if show_mask:
        return deband_mask

    deband = placebo_debander(clip, radius=rad, threshold=thr, grain=grain, iterations=itr)
    deband_masked = core.std.MaskedMerge(deband, clip, deband_mask)
    deband_masked = deband_masked if bits == 16 else depth(deband_masked, bits)
    return deband_masked
