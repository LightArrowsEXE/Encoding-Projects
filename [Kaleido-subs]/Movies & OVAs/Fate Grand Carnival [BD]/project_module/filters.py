from fractions import Fraction
from functools import partial
from typing import Any, Dict, List, Optional, Tuple, Union

from vsutil import fallback, depth, get_depth, get_y, join, plane, iterate, insert_clip

import vapoursynth as vs
import vardefunc as vdf

from .util import _get_bits

core = vs.core


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
    bits, clip = _get_bits(clip)

    clip_y = get_y(clip)
    pf = core.bilateral.Gaussian(clip_y, sigma=pf_sigma) if pf_sigma else clip_y
    ret = core.retinex.MSRCP(pf, sigma=rxsigma, upper_thr=0.005)

    blur_ret = core.bilateral.Gaussian(ret, sigma=sigma)
    blur_ret_diff = core.std.Expr([blur_ret, ret], "x y -")
    blur_ret_dfl = core.std.Deflate(blur_ret_diff)
    blur_ret_ifl = iterate(blur_ret_dfl, core.std.Inflate, 4)
    blur_ret_brz = core.std.Binarize(blur_ret_ifl, brz[0])
    # blur_ret_brz = core.morpho.Close(blur_ret_brz, size=8)

    prewitt_mask = core.std.Prewitt(clip_y).std.Binarize(brz[1])
    prewitt_ifl = prewitt_mask.std.Deflate().std.Inflate()
    prewitt_brz = core.std.Binarize(prewitt_ifl, brz[1])
    # prewitt_brz = core.morpho.Close(prewitt_brz, size=4)

    merged = core.std.Expr([blur_ret_brz, prewitt_brz], "x y +")
    rm_grain = core.rgvs.RemoveGrain(merged, rg_mode)
    return rm_grain if bits == 16 else depth(rm_grain, bits)


def shift_chroma(clip: vs.VideoNode, left: float = 0.0, top: float = 0.0):
    shift = core.resize.Bicubic(clip, src_left=left, src_top=top)
    return core.std.ShufflePlanes([clip, shift], [0, 1, 2], vs.YUV)


def placebo_debander(clip: vs.VideoNode, grain: int = 4, **deband_args: Any) -> vs.VideoNode:
    return join([  # Still not sure why splitting it up into planes is faster, but hey!
        core.placebo.Deband(plane(clip, 0), grain=grain, **deband_args),
        core.placebo.Deband(plane(clip, 1), grain=0, **deband_args),
        core.placebo.Deband(plane(clip, 2), grain=0, **deband_args)
    ])


def mt_xxpand_multi(clip: vs.VideoNode, # noqa
                    sw: int = 1, sh: Optional[int] = None,
                    mode: str = 'square',
                    planes: Union[List[range], int, None] = None, start: int = 0,
                    M__imum: Any = core.std.Maximum,
                    **params: Any) -> List[vs.VideoNode]:
    sh = fallback(sh, sw)
    assert clip.format is not None
    planes = [range(clip.format.num_planes)] or planes

    if mode == 'ellipse':
        coordinates = [[1]*8, [0, 1, 0, 1, 1, 0, 1, 0],
                       [0, 1, 0, 1, 1, 0, 1, 0]]
    elif mode == 'losange':
        coordinates = [[0, 1, 0, 1, 1, 0, 1, 0]] * 3
    else:
        coordinates = [[1]*8] * 3

    clips = [clip]
    end = min(sw, sh) + start

    for x in range(start, end):
        clips += [M__imum(clips[-1], coordinates=coordinates[x % 3], planes=planes, **params)]
    for x in range(end, end + sw - sh):
        clips += [M__imum(clips[-1], coordinates=[0, 0, 0, 1, 1, 0, 0, 0], planes=planes, **params)]
    for x in range(end, end + sh - sw):
        clips += [M__imum(clips[-1], coordinates=[0, 1, 0, 0, 0, 0, 1, 0], planes=planes, **params)]
    return clips


maxm = partial(mt_xxpand_multi, M__imum=core.std.Maximum)
minm = partial(mt_xxpand_multi, M__imum=core.std.Minimum)


def zzdeband(clip: vs.VideoNode, denoised: bool = False, mask: int = 0,
             f3kdb_args: Dict[str, Any] = {}, placebo_args: Dict[str, Any] = {}
             ) -> Union[vs.VideoNode, Any]:
    """
    Written by Zastin, *CAUTIOUSLY* modified by puny little me

    This is all pure black magic to me,
    so I'm just gonna pretend I didn't see anything.
    """
    import zzfunc as zzf

    plcbo_args: Dict[str, Any] = dict(iterations=3, threshold=5, radius=16, grain=0)
    plcbo_args.update(placebo_args)

    dumb3kdb_args: Dict[str, Any] = dict(radius=16, threshold=[30, 0], grain=0)
    dumb3kdb_args.update(f3kdb_args)

    brz = 256 if denoised else 384

    clip_depth = get_depth(clip)
    if clip_depth != 16:
        clip = depth(clip, 16)

    clip_y = plane(clip, 0)

    ymax = maxm(clip_y, sw=30, mode='ellipse')
    ymin = minm(clip_y, sw=30, mode='ellipse')

    # edge detection
    thr = 3.2 * 256
    ypw0 = clip_y.std.Prewitt()
    ypw = ypw0.std.Binarize(thr).rgvs.RemoveGrain(11)
    if mask == 1:
        return ypw

    # range masks (neighborhood max - min)
    rad, thr = 3, 2.5 * 256
    yrangesml = core.std.Expr([ymax[3], ymin[3]], 'x y - abs')
    yrangesml = yrangesml.std.Binarize(thr).std.BoxBlur(0, 2, 1, 2, 1)
    if mask == 2:
        return yrangesml

    rad, thr = 14, 6.5 * 256
    yrangebig0 = core.std.Expr([ymax[rad], ymin[rad]], 'x y - abs')
    yrangebig = yrangebig0.std.Binarize(thr)
    yrangebig = minm(yrangebig, sw=rad * 3 // 4, threshold=65536 // ((rad * 3 // 4) + 1), mode='ellipse')[-1]
    yrangebig = yrangebig.std.BoxBlur(0, rad//4, 1, rad//4, 1)
    if mask == 3:
        return yrangebig

    # morphological masks (shapes)
    rad = 30
    ymph = core.std.Expr([clip_y, maxm(ymin[rad], sw=rad, mode='ellipse')[rad],
                         minm(ymax[rad], sw=rad, mode='ellipse')[rad]], 'x y - z x - max')
    ymph = ymph.std.Binarize(brz)
    ymph = ymph.std.Minimum().std.Maximum()
    ymph = ymph.std.BoxBlur(0, 4, 1, 4, 1)
    if mask == 4:
        return ymph

    grad_mask = zzf.combine([ymph, yrangesml, ypw])
    if mask == 5:
        return grad_mask

    ydebn_strong = clip_y.placebo.Deband(1, **plcbo_args)
    ydebn_normal = vdf.deband.dumb3kdb(clip_y, **dumb3kdb_args)
    ydebn = ydebn_strong.std.MaskedMerge(ydebn_normal, grad_mask)
    ydebn = ydebn.std.MaskedMerge(clip_y, yrangebig)

    merged = join([ydebn, plane(clip, 1), plane(clip, 2)])
    return merged if clip_depth == 16 else depth(merged, clip_depth)


def panner_x(clip: vs.VideoNode, image: str,
             fps: Fraction = Fraction(30000, 1001),
             acc: float = 1.0) -> vs.VideoNode:
    """Written by Varde, stolen by yours truly (and slightly adjusted)"""
    from havsfunc import ChangeFPS

    clip60 = ChangeFPS(clip, fps.numerator, fps.denominator)
    panlarge = core.imwri.Read(image)

    step_x = (panlarge.width - 1920) / clip60.num_frames
    newpan = core.std.BlankClip(panlarge, 1920, 1080, length=1)
    for i in range(clip60.num_frames):
        acc = (i / clip60.num_frames) ** acc

        x_e, x_v = divmod(i * step_x, 1)
        crop = core.std.CropAbs(panlarge, 1921, 1080, int(x_e), 0)
        newpan += core.resize.Bicubic(crop, src_left=x_v).std.Crop(right=1)

    return core.std.AssumeFPS(newpan[1:], clip60).resize.Bicubic(format=vs.YUV420P16, matrix=1)


def fader(clip: vs.VideoNode,
          start_frame: int, end_frame: int,
          duration: Optional[int] = None, input_frame: Optional[int] = None
          ) -> vs.VideoNode:
    """
    A function to fade a part of a given clip into itself.
    Hyper specific, and probably only useful for clip-to-black fades or something.

    start_frame and end_frame are for trimming the clip. Exclusive.
    duration determines how long the fade is.
    input_frame determines where in the clip the faded clip gets inserted.
    """
    import kagefunc as kgf

    duration = duration or (end_frame - start_frame)
    input_frame = input_frame or start_frame

    fade = kgf.crossfade(clip[start_frame] * duration, clip[end_frame] * duration, duration - 1)
    return insert_clip(clip, fade, input_frame)


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
