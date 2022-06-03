from typing import Any, Callable, Dict, List, Optional, Union

import lvsfunc as lvf
import vapoursynth as vs
import vardefunc as vdf
from vsutil import depth, get_y, join, plane

from .util import _get_bits

core = vs.core


def obliaa(clip: vs.VideoNode, mask_clip: Optional[vs.VideoNode] = None,
           sangnom: bool = False, opencl: bool = True,
           downscaler: Callable[[vs.VideoNode, int, int], vs.VideoNode] = lvf.scale.ssim_downsample,
           eedi3_args: Dict[str, Any] = {}, sangnom_args: Dict[str, Any] = {}) -> vs.VideoNode:
    """
    Short for "obliterate with AA". Really, just a simple masked eedi3 + sangnom wrapper.
    """
    clip_y = get_y(clip)
    supersample = vdf.aa.Nnedi3SS(opencl=opencl, shifter=lvf.kernels.Catrom()) \
        .scale(clip_y, clip_y.width*2, clip_y.height*2)

    aa_clip = vdf.aa.Eedi3SR(**eedi3_args).aa(supersample)

    if sangnom:
        aa_clip = vdf.aa.SangNomSR(**sangnom_args).aa(aa_clip)

    if not mask_clip:
        mask_clip = core.std.Prewitt(supersample)
    else:
        mask_clip = lvf.kernels.Catrom(format=aa_clip.format).scale(mask_clip, aa_clip.width, aa_clip.height)

    masked_aa = core.std.MaskedMerge(supersample, aa_clip, mask_clip)
    masked_aa = downscaler(masked_aa, clip.width, clip.height)
    masked_aa = lvf.kernels.Catrom().resample(masked_aa, clip_y.format)

    if clip.format.num_planes == 1:
        return masked_aa
    return vdf.misc.merge_chroma(masked_aa, clip)


def masked_f3kdb(clip: vs.VideoNode,
                 rad: int = 16,
                 thr: Union[int, List[int]] = 24,
                 grain: Union[int, List[int]] = [12, 0],
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
                   rad: int = 12, thr: Union[int, List[int]] = 4,
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


def shift_chroma(clip: vs.VideoNode, src_left: float = 0.0, src_top: float = 0.0) -> vs.VideoNode:
    shift = lvf.kernels.Catrom().shift(clip, (src_top, src_left))
    return core.std.ShufflePlanes([clip, shift], [0, 1, 2], vs.YUV)
