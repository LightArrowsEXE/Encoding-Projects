"""Mostly helper functions"""
from typing import Any, List, Tuple

import vapoursynth as vs
from lvsfunc.types import Range

core = vs.core


def dehardsub(hard: vs.VideoNode, clean: vs.VideoNode,
              signs: List[Range] = [], replace_scenes: List[Range] = [],
              highpass: int = 600, showmask: int = 0) -> Any:
    """
    Basic multi-dehardsubbing function
    """
    from functools import partial

    import kagefunc as kgf
    from lvsfunc.util import quick_resample, replace_ranges

    hardsubmask = kgf.hardsubmask(hard, clean)
    if showmask == 1:
        return hardsubmask
    clip = core.std.MaskedMerge(hard, clean, hardsubmask)

    if signs:
        hardsubmask_fade = quick_resample(
            clip, partial(
                kgf.hardsubmask_fades, ref=clean,
                expand_n=15, highpass=highpass))

        if showmask == 2:
            return hardsubmask_fade

        clip_fade = core.std.MaskedMerge(clip, clean, hardsubmask_fade)
        clip = replace_ranges(clip, clip_fade, ranges=signs)

    if replace_scenes:
        return replace_ranges(clip, clean, ranges=replace_scenes)
    return clip


def _get_bits(clip: vs.VideoNode, expected_depth: int = 16) -> Tuple[int, vs.VideoNode]:
    """Checks bitdepth, set bitdepth if necessary, and sends original clip's bits back with the clip"""
    from vsutil import depth, get_depth

    bits = get_depth(clip)
    return bits, depth(clip, expected_depth) if bits != expected_depth else clip
