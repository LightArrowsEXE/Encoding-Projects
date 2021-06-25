from functools import partial
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import vapoursynth as vs
from vsutil import depth, fallback, join, plane

core = vs.core


def rescaler(clip: vs.VideoNode, height: int) -> vs.VideoNode:
    """
    Basic rescaling function using nnedi3.
    """
    from lvsfunc.kernels import Bicubic, BicubicSharp
    from vardefunc.mask import FDOG
    from vardefunc.scale import nnedi3_upscale
    from vsutil import Range, depth, get_w, get_y

    clip = depth(clip, 32)

    clip_y = get_y(clip)
    descale = BicubicSharp().descale(clip_y, get_w(height, clip.width/clip.height), height)
    rescale = Bicubic(b=-1/2, c=1/4).scale(nnedi3_upscale(descale, pscrn=1), clip.width, clip.height)

    l_mask = FDOG().get_mask(clip_y, lthr=0.065, hthr=0.065).std.Maximum().std.Minimum()
    l_mask = l_mask.std.Median().std.Convolution([1] * 9)  # stolen from varde xd
    masked_rescale = core.std.MaskedMerge(clip_y, rescale, l_mask)

    scaled = join([masked_rescale, plane(clip, 1), plane(clip, 2)])

    return depth(scaled, 16)


def denoiser(clip: vs.VideoNode,
             bm3d_sigma: Union[float, List[float]] = 0.5, bm3d_rad: int = 2,
             dec_sigma: float = 8.0, dec_min: int = 192 << 8, dec_max: int = 232 << 8,
             SMD_args: Dict[str, Any] = {}) -> vs.VideoNode:
    from havsfunc import SMDegrain
    from lvsfunc.denoise import bm3d
    from vardefunc.noise import decsiz

    ref_args: Dict[str, Any] = dict(tr=3, thSAD=150, thSADC=200, contrasharp=16, pel=4, subpixel=3)
    ref_args |= SMD_args

    ref = SMDegrain(clip, **ref_args)
    denoise = bm3d(clip, sigma=bm3d_sigma, radius=bm3d_rad, ref=ref)
    return decsiz(denoise, sigmaS=dec_sigma, min_in=dec_min, max_in=dec_max)


def clamped_aa(clip: vs.VideoNode, rep: int = 17, strength: float = 1.0, **sraa_args: Dict[str, Any]) -> vs.VideoNode:
    from lvsfunc.aa import clamp_aa, nnedi3, taa, upscaled_sraa

    aa_args: Dict[str, Any] = dict(rfactor=1.35)
    aa_args |= sraa_args

    aa_weak = taa(clip, nnedi3(opencl=True))
    aa_strong = upscaled_sraa(clip, **aa_args)
    aa_clamped = clamp_aa(clip, aa_weak, aa_strong, strength=strength)
    return core.rgvs.Repair(aa_clamped, clip, rep)


def transpose_sraa(clip: vs.VideoNode, **aa_args: Dict[str, Any]) -> vs.VideoNode:
    from lvsfunc.aa import upscaled_sraa
    from lvsfunc.kernels import Bicubic

    sraa_args: Dict[str, Any] = dict(rfactor=1.3, downscaler=Bicubic().scale)
    sraa_args |= aa_args

    aa = upscaled_sraa(clip.std.Transpose(), **sraa_args)
    return upscaled_sraa(aa.std.Transpose(), **sraa_args)


def placebo_debander(clip: vs.VideoNode, grain: float = 4.0, deband_args: Dict[str, Any] = {}) -> vs.VideoNode:
    placebo_args: Dict[str, Any] = dict()
    placebo_args |= deband_args

    return join([
        core.placebo.Deband(plane(clip, 0), grain=grain, **placebo_args),
        core.placebo.Deband(plane(clip, 1), grain=0, **placebo_args),
        core.placebo.Deband(plane(clip, 2), grain=0, **placebo_args)
    ])


def mt_xxpand_multi(clip: vs.VideoNode,
                    sw: int = 1, sh: Optional[int] = None,
                    mode: str = 'square',
                    planes: Optional[List[int]] = None, start: int = 0,
                    M__imum: Callable[[vs.VideoNode, Any, Any], vs.VideoNode] = core.std.Maximum,
                    **params: Any) -> List[vs.VideoNode]:
    sh = fallback(sh, sw)

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
        clips += [M__imum(clips[-1], coordinates=coordinates[x % 3], **params)]  # type: ignore[call-arg]  # I can't be assed to sort this one out. Zastin pls  # noqa
    for x in range(end, end + sw - sh):
        clips += [M__imum(clips[-1], coordinates=[0, 0, 0, 1, 1, 0, 0, 0], **params)]  # type: ignore[call-arg]  # I can't be assed to sort this one out. Zastin pls  # noqa
    for x in range(end, end + sh - sw):
        clips += [M__imum(clips[-1], coordinates=[0, 1, 0, 0, 0, 0, 1, 0], **params)]  # type: ignore[call-arg]  # I can't be assed to sort this one out. Zastin pls  # noqa
    return clips


maxm = partial(mt_xxpand_multi, M__imum=core.std.Maximum)
minm = partial(mt_xxpand_multi, M__imum=core.std.Minimum)


def masked_deband(clip: vs.VideoNode, denoised: bool = False,
                  deband_args: Dict[str, Any] = {}) -> vs.VideoNode:
    """
    Written by Zastin, *CAUTIOUSLY* modified by puny little me

    This is all pure black magic to me,
    so I'm just gonna pretend I didn't see anything.
    """
    import zzfunc as zzf

    placebo_args: Dict[str, Any] = dict(iterations=2, threshold=4.0, radius=12, grain=4.0)
    placebo_args |= deband_args

    brz = 256 if denoised else 384

    assert clip.format is not None

    clip_depth = clip.format.bits_per_sample
    if clip_depth != 16:
        clip = depth(clip, 16)

    clip_y = plane(clip, 0)
    stats = clip_y.std.PlaneStats()
    agm3 = core.adg.Mask(stats, 3)

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
    grain_mask = core.std.Expr([yrangebig, grad_mask, ypw0.std.Binarize(2000).std.Maximum().std.Maximum()],
                               expr='65535 y - x min z -').std.BoxBlur(0, 16, 1, 16, 1)

    ydebn_strong = clip_y.placebo.Deband(1, **placebo_args)

    ydebn_normal = clip_y.f3kdb.Deband(16, 41, 0, 0, 0, 0, output_depth=16)
    ydebn = ydebn_strong.std.MaskedMerge(ydebn_normal, grad_mask)
    ydebn = ydebn.std.MaskedMerge(clip_y, yrangebig)

    strong_grain = ydebn_strong.grain.Add(0.25, constant=True, seed=69420)
    normal_grain = ydebn.std.MaskedMerge(ydebn.grain.Add(0.1, constant=True, seed=69420), agm3)
    y_final = normal_grain.std.MaskedMerge(strong_grain, grain_mask)
    merged = join([y_final, plane(clip, 1), plane(clip, 2)])
    return merged if clip_depth == 16 \
        else depth(merged, clip_depth)
