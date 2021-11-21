from typing import Any, List, Optional, Tuple

import vapoursynth as vs

from .util import _get_bits

core = vs.core


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


def rekt(clip: vs.VideoNode) -> vs.VideoNode:
    """Apply rekt consistently across multiple clips"""
    import rekt
    from awsmfunc import bbmod

    rkt = rekt.rektlvls(
        clip,
        [0, 1079], [17, 16],
        [0, 1, 2, 3] + [1917, 1918, 1919], [16, 4, -2, 2] + [-2, 5, 14]
    )
    return bbmod(rkt, left=4, right=3, y=False)


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
    from kagefunc import kirsch
    from vsutil import depth, get_y, iterate

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

    kirsch_mask = kirsch(clip_y).std.Binarize(brz[1])
    kirsch_ifl = kirsch_mask.std.Deflate().std.Inflate()
    kirsch_brz = core.std.Binarize(kirsch_ifl, brz[1])
    kirsch_brz = core.morpho.Close(kirsch_brz, size=4)

    merged = core.std.Expr([blur_ret_brz, kirsch_brz], "x y +")
    rm_grain = core.rgvs.RemoveGrain(merged, rg_mode)
    return rm_grain if bits == 16 else depth(rm_grain, bits)
