from typing import Tuple

import vapoursynth as vs
import yaml


def _get_bits(clip: vs.VideoNode, expected_depth: int = 16) -> Tuple[int, vs.VideoNode]:
    """Checks bitdepth, set bitdepth if necessary, and sends original clip's bitdepth back with the clip"""
    from vsutil import depth, get_depth

    bits = get_depth(clip)
    return bits, depth(clip, expected_depth) if bits != expected_depth else clip
