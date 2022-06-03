from functools import partial
from typing import Any, Dict, List, Union

import lvsfunc as lvf
import vapoursynth as vs
import zzfunc as zzf
from lvsfunc.kernels import Catrom
from vsmask.edge import FDOGTCanny
from vsmask.util import XxpandMode, expand, inpand, max_planes
from vsutil import depth, fallback, get_depth, join, plane, split

from .util import _get_bits

core = vs.core


def mt_xxpand_multi(clip: vs.VideoNode,
                    sw=1, sh=None,
                    mode='square',
                    planes=None, start=0,
                    m__imum=core.std.Maximum,
                    **params) -> List[vs.VideoNode]:
    sh = fallback(sh, sw)
    assert clip.format is not None

    if planes is None:
        planes = list(range(clip.format.num_planes))
    elif isinstance(planes, int):
        planes = [planes]

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
        clips += [m__imum(clips[-1], coordinates=coordinates[x % 3], planes=planes, **params)]
    for x in range(end, end + sw - sh):
        clips += [m__imum(clips[-1], coordinates=[0, 0, 0, 1, 1, 0, 0, 0], planes=planes, **params)]
    for x in range(end, end + sh - sw):
        clips += [m__imum(clips[-1], coordinates=[0, 1, 0, 0, 0, 0, 1, 0], planes=planes, **params)]
    return clips


maxm = partial(mt_xxpand_multi, m__imum=core.std.Maximum)
minm = partial(mt_xxpand_multi, m__imum=core.std.Minimum)


def morpho_dbm(clip: vs.VideoNode, denoised: bool = False, **deband_args) -> vs.VideoNode:
    """
    Written by Zastin, *CAUTIOUSLY* modified by puny little me

    This is all pure black magic to me,
    so I'm just gonna pretend I didn't see anything.
    """
    placebo_args = dict(iterations=3, threshold=5, radius=16, grain=0)
    placebo_args.update(deband_args)

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

    # range masks (neighborhood max - min)
    rad, thr = 3, 2.5 * 256
    yrangesml = core.std.Expr([ymax[3], ymin[3]], 'x y - abs')
    yrangesml = yrangesml.std.Binarize(thr).std.BoxBlur(0, 2, 1, 2, 1)

    rad, thr = 16, 4 * 256
    yrangebig0 = core.std.Expr([ymax[rad], ymin[rad]], 'x y - abs')
    yrangebig = yrangebig0.std.Binarize(thr)
    yrangebig = minm(yrangebig, sw=rad * 3 // 4, threshold=65536 // ((rad * 3 // 4) + 1), mode='ellipse')[-1]
    yrangebig = yrangebig.std.BoxBlur(0, rad//4, 1, rad//4, 1)

    # morphological masks (shapes)
    rad, thr = 30, 1 * 256
    ymph = core.std.Expr([clip_y, maxm(ymin[rad], sw=rad, mode='ellipse')[rad],
                         minm(ymax[rad], sw=rad, mode='ellipse')[rad]], 'x y - z x - max')
    ymph = ymph.std.Binarize(brz)
    ymph = ymph.std.Minimum().std.Maximum()
    ymph = ymph.std.BoxBlur(0, 4, 1, 4, 1)

    grad_mask = zzf.combine([ymph, yrangesml, ypw])

    return grad_mask, yrangebig


def masked_f3kdb(clip: vs.VideoNode,
                 rad: int = 16,
                 thr: Union[int, List[int]] = 24,
                 grain: Union[int, List[int]] = [12, 0],
                 mask_args: Dict[str, Any] = {}
                 ) -> vs.VideoNode:
    """Basic f3kdb debanding with detail mask """
    from debandshit import dumb3kdb

    deb_mask_args: Dict[str, Any] = dict(brz=(1000, 2750))
    deb_mask_args |= mask_args

    bits, clip = _get_bits(clip)

    deband_mask = lvf.mask.detail_mask_neo(clip, **deb_mask_args)

    deband = dumb3kdb(clip, radius=rad, threshold=thr, grain=grain)
    deband_masked = core.std.MaskedMerge(deband, clip, deband_mask)
    deband_masked = deband_masked if bits == 16 else depth(deband_masked, bits)
    return deband_masked


def placebo_debander(clip: vs.VideoNode, grain: int = 4, **deband_args: Any) -> vs.VideoNode:
    return join([  # Still not sure why splitting it up into planes is faster, but hey! It works!
        core.placebo.Deband(plane(clip, 0), grain=grain, **deband_args),
        core.placebo.Deband(plane(clip, 1), grain=0, **deband_args),
        core.placebo.Deband(plane(clip, 2), grain=0, **deband_args)
    ])


def masked_placebo(clip: vs.VideoNode,
                   rad: int = 12, thr: Union[int, List[int]] = 4,
                   itr: int = 2, grain: int = 2,
                   mask_args: Dict[str, Any] = {},
                   show_mask: bool = False,
                   ) -> vs.VideoNode:
    """Basic placebo debanding with detail mask"""
    deb_mask_args: Dict[str, Any] = dict(brz=(2250, 4500))
    deb_mask_args |= mask_args

    bits, clip = _get_bits(clip)

    deband_mask = lvf.mask.detail_mask_neo(clip, **deb_mask_args)
    if show_mask:
        return deband_mask

    deband = placebo_debander(clip, radius=rad, threshold=thr, grain=grain, iterations=itr)
    deband_masked = core.std.MaskedMerge(deband, clip, deband_mask)
    deband_masked = deband_masked if bits == 16 else depth(deband_masked, bits)
    return deband_masked


# The following functions were written by Varde. Man's an absolute madlad
def to_hsv(clip: vs.VideoNode) -> vs.VideoNode:
    planes = split(clip.std.RemoveFrameProps('_Matrix'))
    cmax = core.std.Expr(planes, 'x y z max max')
    cmin = core.std.Expr(planes, 'x y z min min')
    Δ = core.std.Expr([cmax, cmin], 'x y -')

    rc = core.std.Expr([cmax, planes[0], Δ], 'x y - z /')
    gc = core.std.Expr([cmax, planes[1], Δ], 'x y - z /')
    bc = core.std.Expr([cmax, planes[2], Δ], 'x y - z /')
    # x y z  |  a  b  c  d    e
    # r g b  |  rc gc bc cmax Δ
    h = core.std.Expr(planes + [rc, gc, bc, cmax, Δ], 'e 0 = 0 d x = c z - d y = 2 a + c - 4 z + a - ? ? ? 6 /')
    # h = core.std.Expr(planes + [rc, gc, bc, cmax], 'cmax r = bc gc - cmax g = 2 rc + bc - 4 gc + rc - ? ? 6 /')
    h = core.std.Expr(h, 'x 0 < x 1 + x ?')
    s = core.std.Expr([Δ, cmax], 'y 0 = 0 x y / ?')
    v = cmax
    return join([h, s, v])


def red_mask(clip: vs.VideoNode,
             h_thr: float = 20 / 255,
             s_hr: float = 80 / 255,
             v_thrl: float = 255 / 255,
             v_thrh: float = 15 / 255) -> vs.VideoNode:
    clip_rgb = clip.resize.Bicubic(format=vs.RGBS).std.RemoveFrameProps('_Matrix')
    clip_hsv = to_hsv(clip_rgb)

    cclip = core.std.Expr(
        split(clip_hsv), f'x {h_thr} < x 1 {h_thr} - > or y {s_hr} > and z {v_thrl} < z {v_thrh} > and and 1 0 ?'
    )

    cclip = expand(cclip, 20, 20, XxpandMode.ELLIPSE)
    cclip = inpand(cclip, 15, 15, XxpandMode.ELLIPSE)

    edgemask = max_planes(
        *split(FDOGTCanny().get_mask(clip).std.RemoveFrameProps('_Matrix'))
    ).std.Binarize(0.4).std.Maximum().std.Minimum()

    return core.std.Expr([cclip, edgemask], 'x 1 >= y 1 >= and x 0 ?').std.Limiter(0, 1, [0, 1, 2])


def chroma_shifter(clip: vs.VideoNode, src_left: float = 0.0, src_top: float = 0.0) -> vs.VideoNode:
    """
    Very simple chroma shift wrapper.

    :param clip:        Input clip
    :param src_left:    Amount of pixels to shift the chroma to the left
    :param src_top:     Amount of pixels to shift the chroma upwards

    :return:            Clip with chroma shifted
    """
    shift = Catrom().shift(clip, (src_top, src_left))
    return core.std.ShufflePlanes([clip, shift], [0, 1, 2], vs.YUV)
