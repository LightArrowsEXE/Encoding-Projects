from functools import partial
from typing import Any, Callable, Dict, List, Optional, Union

import lvsfunc as lvf
import vapoursynth as vs
import vardefunc as vdf
from lvsfunc.kernels import BicubicSharp, Kernel, Spline36
from lvsfunc.util import get_prop
from vsutil import depth, get_w, get_y, iterate, join, plane

from .util import _get_bits

core = vs.core


def conditional_descale(clip: vs.VideoNode, height: int = 720,
                        kernel: Kernel = Spline36, thr: float = 0.000015) -> vs.VideoNode:
    """
    Quick wrapper to descale to SharpBicubic and an additional kernel,
    compare them, and then pick one or the other.

    :param clip:        Input clip
    :param height:      Descale height
    :param kernel:      Kernel to compare BicubicSharp to
    :param thr:         Threshold for which kernel to pick
    """
    def _compare(n: int, f: vs.VideoFrame, sharp: vs.VideoNode, other: vs.VideoNode) -> vs.VideoNode:
        sharp_diff = get_prop(f[0], 'PlaneStatsDiff', float)
        other_diff = get_prop(f[1], 'PlaneStatsDiff', float)

        return sharp if other_diff - thr > sharp_diff else other

    if kernel == BicubicSharp:
        raise ValueError(f"conditional_descale: 'You may not compare BicubicSharp with {kernel.__name__}!'")

    clip_y = get_y(clip)
    sharp = BicubicSharp().descale(clip_y, get_w(height, clip.width/clip.height), height)
    sharp_up = BicubicSharp().scale(sharp, clip.width, clip.height)

    other = kernel().descale(clip_y, get_w(height, clip.width/clip.height), height)
    other_up = kernel().scale(other, clip.width, clip.height)

    # We need a diff between the rescaled clips and the original clip
    sharp_diff = core.std.PlaneStats(sharp_up, clip_y)
    other_diff = core.std.PlaneStats(other_up, clip_y)

    # Extra props for future frame evalling in case it might prove useful (for credits, for example)
    sharp = sharp.std.SetFrameProp('scaler', data=BicubicSharp().__class__.__name__)
    other = other.std.SetFrameProp('scaler', data=kernel().__class__.__name__)

    return core.std.FrameEval(sharp, partial(_compare, sharp=sharp, other=other), [sharp_diff, other_diff])


def conditional_restore(clip: vs.VideoNode, height: int = 1080, kernel: Kernel = Spline36) -> vs.VideoNode:
    """
    Function to go with conditional_descale to reupscale the clip for descale detail masking.
    """
    if kernel == BicubicSharp:
        raise ValueError(f"conditional_restore: 'You may not compare BicubicSharp with {kernel.__name__}!'")

    def _compare(n: int, f: vs.VideoFrame, sharp_up: vs.VideoNode, other_up: vs.VideoNode) -> vs.VideoNode:
        return sharp_up if get_prop(f, 'scaler', bytes) == b'BicubicSharp' else other_up

    sharp_up = BicubicSharp().scale(clip, get_w(height, clip.width/clip.height), height)
    other_up = kernel().scale(clip, get_w(height, clip.width/clip.height), height)

    sharp_up = sharp_up.std.SetFrameProp('upscaler', data=f'{BicubicSharp().__class__.__name__}')
    other_up = other_up.std.SetFrameProp('upscaler', data=f'{kernel().__class__.__name__}')

    return core.std.FrameEval(sharp_up, partial(_compare, sharp_up=sharp_up, other_up=other_up), clip)


def conditional_aa(clip: vs.VideoNode, strength: float = 1.5,
                   shader_file: str = "FSRCNNX_x2_56-16-4-1.glsl", rmode: int = 13,
                   baa_args: Dict[str, Any] = {}, sraa_args: Dict[str, Any] = {}) -> vs.VideoNode:
    """
    Function to go with conditional_descale to AA only the scenes that were upscaled using BicubicSharp.
    """
    def _compare(n: int, f: vs.VideoFrame, clip: vs.VideoNode, aa_clip: vs.VideoNode) -> vs.VideoNode:
        return aa_clip if get_prop(f, 'scaler', bytes) == b'BicubicSharp' else clip

    baa = lvf.aa.based_aa(clip, shader_file, **baa_args)
    sraa = lvf.sraa(clip, **sraa_args)
    aa_clip = lvf.aa.clamp_aa(clip, baa, sraa, strength=strength)
    aa_clip = core.rgvs.Repair(aa_clip, clip, rmode)

    return core.std.FrameEval(clip, partial(_compare, clip=clip, aa_clip=aa_clip), clip)


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


def detail_mask(clip: vs.VideoNode, sigma: float = 1.0,
                detail_brz: int = 2500, lines_brz: int = 4500,
                blur_func: Callable[[vs.VideoNode, vs.VideoNode, float],
                                    vs.VideoNode] = core.bilateral.Bilateral,
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

    deband_mask = detail_mask(clip, **deb_mask_args)
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
    from vsutil import depth

    deb_mask_args: Dict[str, Any] = dict(detail_brz=2250, lines_brz=4500)
    deb_mask_args |= mask_args

    bits, clip = _get_bits(clip)

    deband_mask = detail_mask(clip, **deb_mask_args)
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
