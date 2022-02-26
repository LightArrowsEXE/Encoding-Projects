from functools import partial
from typing import Any, Callable, Dict, List, Optional, Union

import vapoursynth as vs
from vsutil import depth, get_depth

from .util import _get_bits

core = vs.core


def detail_mask(clip: vs.VideoNode, sigma: float = 1.0,
                detail_brz: int = 2500, lines_brz: int = 4500,
                blur_func: Callable[[vs.VideoNode, vs.VideoNode, float],
                                    vs.VideoNode] = core.bilateral.Bilateral,  # type: ignore
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
    import lvsfunc as lvf
    from vsutil import get_y, iterate

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

    deb_mask_args: Dict[str, Any] = dict(brz=(1000, 2750))
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
    from vsutil import join, plane
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
    assert clip.format is not None
    planes = [x for x in range(clip.format.num_planes)] or planes

    if mode == 'ellipse':
        coordinates = [[1]*8, [0, 1, 0, 1, 1, 0, 1, 0],
                       [0, 1, 0, 1, 1, 0, 1, 0]]
    elif mode == 'losange':
        coordinates = [[0, 1, 0, 1, 1, 0, 1, 0]] * 3
    else:
        coordinates = [[1]*8] * 3

    clips = [clip]
    sh = sw if sh is None else sh
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
    from debandshit.debanders import dumb3kdb
    from vsutil import depth, get_depth, join, plane

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
    ydebn_normal = dumb3kdb(clip_y, **dumb3kdb_args)
    ydebn = ydebn_strong.std.MaskedMerge(ydebn_normal, grad_mask)
    ydebn = ydebn.std.MaskedMerge(clip_y, yrangebig)

    merged = join([ydebn, plane(clip, 1), plane(clip, 2)])
    return merged if clip_depth == 16 else depth(merged, clip_depth)


def multi_debander(clip: vs.VideoNode, old_clip: vs.VideoNode) -> vs.VideoNode:
    from debandshit.debanders import dumb3kdb
    from vsutil import get_y, join, plane

    mask = detail_mask(old_clip, brz=(1000, 3000), pf_sigma=False)

    deband = dumb3kdb(get_y(clip), radius=17, threshold=[28, 0], grain=[16, 0])
    deband_chr = placebo_debander(clip, iterations=2, threshold=3, radius=16, grain=0)
    deband = join([deband, plane(deband_chr, 1), plane(deband_chr, 2)])

    return core.std.MaskedMerge(deband, clip, mask)


def selector(clip: vs.VideoNode, flt: vs.VideoNode) -> vs.VideoNode:
    from lvsfunc.util import get_prop

    def _select(n: int, f: vs.VideoFrame, src: vs.VideoNode, flt: vs.VideoNode, crop: vs.VideoNode) -> vs.VideoNode:
        psmax = get_prop(crop.get_frame(n), 'PlaneStatsMax', int)
        return src if psmax == 16 << (get_depth(src) - 8) else flt

    crop = core.std.CropRel(clip, bottom=clip.height/6*5)
    crop = crop.std.PlaneStats()

    src = clip.std.SetFrameProp('Filtered', intval=0)
    flt = flt.std.SetFrameProp('Filtered', intval=1)

    return core.std.FrameEval(src, partial(_select, src=src, flt=flt, crop=crop), crop)
