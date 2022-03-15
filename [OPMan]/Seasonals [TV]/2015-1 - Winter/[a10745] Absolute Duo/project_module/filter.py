from __future__ import annotations

from typing import Any, Dict, List

import lvsfunc as lvf
import vapoursynth as vs
from vsutil import depth, join, plane

from .util import _get_bits

core = vs.core


def masked_f3kdb(clip: vs.VideoNode,
                 rad: int = 16,
                 thr: int | List[int] = 24,
                 grain: int | List[int] = [12, 0],
                 mask_args: Dict[str, Any] = {},
                 show_mask: bool = False
                 ) -> vs.VideoNode:
    """Basic f3kdb debanding with detail mask"""
    from debandshit import dumb3kdb
    from vsutil import depth

    deb_mask_args: Dict[str, Any] = dict(detail_brz=1000, lines_brz=2750)
    deb_mask_args |= mask_args

    bits, clip = _get_bits(clip)

    deband_mask = lvf.mask.detail_mask_neo(clip, **deb_mask_args)
    if show_mask:
        return deband_mask

    deband = dumb3kdb(clip, radius=rad, threshold=thr, grain=grain)
    deband_masked = core.std.MaskedMerge(deband, clip, deband_mask)
    deband_masked = deband_masked if bits == 16 else depth(deband_masked, bits)
    return deband_masked


def masked_placebo(clip: vs.VideoNode,
                   rad: int = 12, thr: int | List[int] = 4,
                   itr: int = 2, grain: int = 2,
                   mask_args: Dict[str, Any] = {},
                   show_mask: bool = False,
                   ) -> vs.VideoNode:
    """Basic placebo debanding with detail mask"""
    deb_mask_args: Dict[str, Any] = dict(detail_brz=2250, lines_brz=4500)
    deb_mask_args |= mask_args

    bits, clip = _get_bits(clip)

    deband_mask = lvf.mask.detail_mask_neo(clip, **deb_mask_args)

    if show_mask:
        return deband_mask

    deband = placebo_debander(clip, radius=rad, threshold=thr, grain=grain, iterations=itr)
    deband_masked = core.std.MaskedMerge(deband, clip, deband_mask)
    deband_masked = deband_masked if bits == 16 else depth(deband_masked, bits)
    return deband_masked


def placebo_debander(clip: vs.VideoNode, grain: int = 4, **deband_args: Any) -> vs.VideoNode:
    if clip.format.num_planes == 1:
        return core.placebo.Deband(clip, grain=grain, **deband_args)

    return join([  # Still not sure why splitting it up into planes is faster, but hey!
        core.placebo.Deband(plane(clip, 0), grain=grain, **deband_args),
        core.placebo.Deband(plane(clip, 1), grain=0, **deband_args),
        core.placebo.Deband(plane(clip, 2), grain=0, **deband_args)
    ])
