from typing import Any, Dict, List, Optional, Tuple, Union, Callable

import vapoursynth as vs
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


def bestframeselect(clips: List[vs.VideoNode], ref: vs.VideoNode,
                    stat_func: Callable[[vs.VideoNode, vs.VideoNode], vs.VideoNode] = core.std.PlaneStats,
                    prop: str = 'PlaneStatsDiff',
                    comp_func: Callable[[float, float], float] = max,
                    debug: bool = False):
    """
    Taken from https://github.com/po5/notvlc/blob/master/notvlc.py#L23 and slightly adjusted

    Picks the 'best' clip for any given frame using stat functions.
    clips: list of clips
    ref: reference clip, e.g. core.average.Mean(clips) / core.median.Median(clips)
    stat_func: function that adds frame properties
    prop: property added by stat_func to compare
    comp_func: function to decide which clip to pick, e.g. min, max
    comp_func: function to decide which value wins, e.g. min, max
    debug: display values of prop for each clip, and which clip was picked
    """
    from functools import partial
    from lvsfunc.util import get_prop

    def _prop_comp(lst, comp_func, prop):
        return comp_func(range(len(lst)), key=lambda i: lst[i][prop])

    def _stats(ref, clips, stat_func):
        scores = []
        for clip in clips:
            diff = stat_func(clip, ref)
            scores.append(diff.get_frame(0).props)
        return scores

    def _select(n, f, ref, stat_func, prop, comp_func, debug=False):
        import vsutil
        clips = list(map(vsutil.frame2clip, f))
        scores = _stats(ref, clips, stat_func)
        best = _prop_comp(scores, comp_func, prop)
        out = f[best]
        if debug:
            out = vsutil.frame2clip(f[best]).text.Text("\n".join([f"Prop: {prop}",
                                                                  *[f"{i}: {s[prop]}"for i, s in enumerate(scores)],
                                                                  f"Best: {best}"])).get_frame(0)
        return out

    return core.std.ModifyFrame(clip=clips[0], clips=clips,
                                selector=partial(_select, ref=ref, stat_func=stat_func, prop=prop,
                                                 comp_func=comp_func, debug=debug))
