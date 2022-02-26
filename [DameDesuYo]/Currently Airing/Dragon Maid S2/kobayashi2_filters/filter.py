"""
    Sub-module for the filtering for the filterchain
"""
from typing import Any, Dict, List, Mapping, Optional, Tuple, Union, cast

import vapoursynth as vs
from vsutil import depth, get_y, join, plane

from .util import _get_bits

core = vs.core


EXPR_VARS: str = 'xyzabcdefghijklmnopqrstuvw'


def bm3d_ref(clip: vs.VideoNode,
             bm3d_sigma: Union[float, List[float]] = 0.5, bm3d_rad: int = 2,
             dec_sigma: float = 8.0, dec_min: int = 192 << 8, dec_max: int = 232 << 8,
             SMD_args: Dict[str, Any] = {}) -> vs.VideoNode:
    from havsfunc import SMDegrain
    from lvsfunc.denoise import bm3d
    from vardefunc.noise import decsiz

    bits, clip = _get_bits(clip)

    ref_args: Dict[str, Any] = dict(tr=3, thSAD=150, thSADC=200, contrasharp=16, pel=4, subpixel=3)
    ref_args |= SMD_args

    ref = SMDegrain(clip, **ref_args)
    denoise = bm3d(clip, sigma=bm3d_sigma, radius=bm3d_rad, ref=ref)
    decs = decsiz(denoise, sigmaS=dec_sigma, min_in=dec_min, max_in=dec_max)
    return decs if bits == 16 else depth(decs, bits)


def masked_f3kdb(clip: vs.VideoNode,
                 rad: int = 16,
                 thr: Union[int, List[int]] = 24,
                 grain: Union[int, List[int]] = [12, 0],
                 mask_args: Dict[str, Any] = {}
                 ) -> vs.VideoNode:
    from vardefunc.deband import dumb3kdb

    deb_mask_args: Dict[str, Any] = dict(brz=(1000, 2750))
    deb_mask_args |= mask_args

    bits, clip = _get_bits(clip)

    deband_mask = detail_mask(clip, **deb_mask_args)

    deband = dumb3kdb(clip, radius=rad, threshold=thr, grain=grain)
    deband_masked = core.std.MaskedMerge(deband, clip, deband_mask)
    deband_masked = deband_masked if bits == 16 else depth(deband_masked, bits)
    return deband_masked


def bidehalo(clip: vs.VideoNode,
             sigma: float = 0.5,
             rad: float = 5 / 255,
             mask_args: Dict[str, Any] = {}
             ) -> vs.VideoNode:
    """"Slight dehalo because >lol it's so freaking sharp"""
    from lvsfunc.dehalo import bidehalo as bidh
    from lvsfunc.mask import halo_mask

    hmask_args: Dict[str, Any] = dict(brz=0.45)
    hmask_args |= mask_args

    dehalo = bidh(clip, sigmaS=sigma, sigmaR=rad)
    mask = halo_mask(clip, **hmask_args)
    return core.std.MaskedMerge(clip, dehalo, mask)


def detail_mask(clip: vs.VideoNode,
                sigma: float = 1.0, rxsigma: List[int] = [50, 200, 350],
                pf_sigma: Optional[float] = 1.0,
                rad: int = 3, brz: Tuple[int, int] = (2500, 4500),
                rg_mode: int = 17,
                ) -> vs.VideoNode:
    """
    A detail mask aimed at preserving as much detail as possible
    within darker areas, even if it contains mostly noise.
    """
    from kagefunc import kirsch
    from vsutil import iterate

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


def default_grain(clip: vs.VideoNode, grain_args: Dict[str, Any] = {}) -> Any:
    """Consistent grainer across episodes"""
    from adptvgrnMod import adptvgrnMod

    g_args: Dict[str, Any] = dict(strength=0.2, luma_scaling=10, size=1.25, sharp=80, grain_chroma=False)
    g_args |= grain_args

    return adptvgrnMod(clip, seed=42069, **g_args)


def placebo_debander(clip: vs.VideoNode, grain: float = 2.0, deband_args: Mapping[str, Any] = {}) -> vs.VideoNode:
    return join([
        core.placebo.Deband(plane(clip, 0), grain=grain, **deband_args),
        core.placebo.Deband(plane(clip, 1), grain=0, **deband_args),
        core.placebo.Deband(plane(clip, 2), grain=0, **deband_args)
    ])


def add_expr(n: int) -> str:
    return 'x y + ' + ' + '.join(EXPR_VARS[i] for i in range(2, n)) + ' +'


def ccd(clip: vs.VideoNode, threshold: float) -> vs.VideoNode:
    """taken from a currently-private gist, but should become available in `vs-denoise` soon enough"""
    from vsutil import split

    assert clip.format
    bits = clip.format.bits_per_sample
    is_float = clip.format.sample_type == vs.FLOAT
    peak = 1.0 if is_float else (1 << bits) - 1
    threshold /= peak
    # threshold = threshold ** 2 / 195075.0

    rgb = clip.resize.Bicubic(format=vs.RGBS)

    pre1 = rgb.resize.Point(
        clip.width+24, clip.height+24,
        src_left=-12, src_top=-12,
        src_width=clip.width+24, src_height=clip.height+24
    )
    pre2 = rgb.resize.Point(
        rgb.width+24, rgb.height+24,
        src_width=rgb.width+24, src_height=rgb.height+24
    )
    pre_planes = split(pre1)

    shift_planes_clips = [
        split(pre2.resize.Point(src_left=-x, src_top=-y))
        for x in range(0, 25, 8) for y in range(0, 25, 8)
    ]
    denoise_clips = [
        core.std.Expr(pre_planes + shift_planes, f'x a - dup * y b - dup * + z c - dup * + sqrt {threshold} <')
        for shift_planes in shift_planes_clips
    ]

    cond_planes_clips = [
        join([core.std.Expr([splane, dclip], 'y 0 > x 0 ?') for splane in splanes])
        for dclip, splanes in zip(denoise_clips, shift_planes_clips)
    ]

    denoise = core.std.Expr(denoise_clips, add_expr(len(denoise_clips)) + ' 1 +')
    denoise = join([denoise] * 3)

    n_op = len(cond_planes_clips) + 1
    avg = core.std.Expr([pre1] + cond_planes_clips + [denoise], add_expr(n_op) + f' {EXPR_VARS[n_op]} /')
    avg = avg.resize.Bicubic(
        format=clip.format.id, dither_type='error_diffusion', matrix=cast(int, clip.get_frame(0).props['_Matrix'])
    )
    avg = avg.std.Crop(12, 12, 12, 12)

    assert avg.format
    return core.std.ShufflePlanes([clip, avg], [0, 1, 2], avg.format.color_family)
