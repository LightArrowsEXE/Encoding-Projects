from functools import partial
from typing import Any, Dict, List, Optional, Tuple, Union

import havsfunc as haf
import lvsfunc as lvf
import vapoursynth as vs
import vardefunc as vdf
from vsutil import (depth, fallback, get_depth, get_w, get_y, insert_clip,
                    iterate, join, plane)

core = vs.core


def rescaler(clip: vs.VideoNode, height: int, shader_file: str) -> Tuple[vs.VideoNode, vs.VideoNode]:
    """
    Basic rescaling and mask generating function using FSRCNNX/nnedi3.

    :param clip:        Source clip
    :param height:      Height to descale to

    :return:            Rescaled clip, descale detail mask
    """
    descale = lvf.kernels.Bicubic().descale(get_y(clip), get_w(height), height)
    rescale_fsrcnx = vdf.scale.fsrcnnx_upscale(descale, shader_file=shader_file)
    rescale_nnedi3 = vdf.scale.nnedi3_upscale(descale, pscrn=1).resize.Bicubic(clip.width, clip.height)
    rescale = core.std.Merge(rescale_fsrcnx, rescale_nnedi3)
    scaled = join([rescale, plane(clip, 1), plane(clip, 2)])

    upscale = lvf.kernels.Bicubic().scale(descale, 1920, 1080)
    detail_mask = lvf.scale.descale_detail_mask(clip, upscale, threshold=0.045)
    return depth(scaled, 16), core.std.Expr(detail_mask, 'x 65535 *', vs.GRAY16)


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
    import kagefunc as kgf

    bits = get_depth(clip)

    if bits != 16:
        clip = depth(clip, 16)

    clip_y = get_y(clip)
    pf = core.bilateral.Gaussian(clip_y, sigma=pf_sigma) if pf_sigma else clip_y
    ret = core.retinex.MSRCP(pf, sigma=rxsigma, upper_thr=0.005)

    blur_ret = core.bilateral.Gaussian(ret, sigma=sigma)
    blur_ret_diff = core.std.Expr([blur_ret, ret], "x y -")
    blur_ret_dfl = core.std.Deflate(blur_ret_diff)
    blur_ret_ifl = iterate(blur_ret_dfl, core.std.Inflate, 4)
    blur_ret_brz = core.std.Binarize(blur_ret_ifl, brz[0])
    blur_ret_brz = core.morpho.Close(blur_ret_brz, size=8)

    kirsch = kgf.kirsch(clip_y).std.Binarize(brz[1])
    kirsch_ifl = core.std.Deflate(kirsch).std.Inflate()
    kirsch_brz = core.std.Binarize(kirsch_ifl, brz[1])
    kirsch_brz = core.morpho.Close(kirsch_brz, size=4)

    morpho_mask = morpho_mask_simple(clip, radius=rad)

    merged = core.std.Expr([blur_ret_brz, kirsch_brz, morpho_mask], "x y + z +")
    rm_grain = core.rgvs.RemoveGrain(merged, rg_mode)
    return rm_grain if bits == 16 else depth(rm_grain, bits)


def morpho_mask_simple(clip: vs.VideoNode, radius: int = 3, **mode: str) -> vs.VideoNode:
    clip_y = plane(clip, 0)
    refa = haf.mt_inpand_multi(haf.mt_expand_multi(clip_y, sw=radius, sh=radius, **mode), sw=radius, sh=radius, **mode)
    refb = haf.mt_expand_multi(haf.mt_inpand_multi(clip_y, sw=radius, sh=radius, **mode), sw=radius, sh=radius, **mode)
    return core.std.Expr([clip_y, refa, refb], 'x y - abs x z - abs max')


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


def panner_x(clip: vs.VideoNode, image: str, acc: float = 1.0) -> vs.VideoNode:
    """Written by Varde, stolen by yours truly"""
    clip60 = haf.ChangeFPS(clip, 60000, 1001)
    panlarge = core.imwri.Read(image)

    step_x = (panlarge.width - 1920) / clip60.num_frames
    newpan = core.std.BlankClip(panlarge, 1920, 1080, length=1)
    for i in range(clip60.num_frames):
        acc = (i / clip60.num_frames) ** acc

        x_e, x_v = divmod(i * step_x, 1)
        crop = core.std.CropAbs(panlarge, 1921, 1080, int(x_e), 0)
        newpan += core.resize.Bicubic(crop, src_left=x_v).std.Crop(right=1)

    return core.std.AssumeFPS(newpan[1:], clip60).resize.Bicubic(format=vs.YUV420P16, matrix=1)


_dfttest_args: Any = dict(smode=0, sosize=0, tbsize=1, tosize=0, tmode=0, planes=[0])
_slocation: List[float] = [0.0, 4, 0.35, 16, 0.4, 512, 1.0, 512]


def extractFrequency(clip: vs.VideoNode,
                     slocation: List[float] = _slocation
                     ) -> vs.VideoNode:
    """
    Denoise certain frequencies
    """
    return core.dfttest.DFTTest(clip, sbsize=9, slocation=slocation, **_dfttest_args)


def mergeFrequency(extracted_clip: vs.VideoNode,
                   denoised_clip: vs.VideoNode,
                   slocation: List[float] = _slocation
                   ) -> vs.VideoNode:
    """
    Merge certain frequences with a denoised clip
    """
    den = core.dfttest.DFTTest(denoised_clip, sbsize=9, slocation=slocation, **_dfttest_args)
    hif = core.std.MakeDiff(denoised_clip, den)
    return core.std.MergeDiff(extracted_clip, hif)


def multi_denoise(clip: vs.VideoNode, mask: vs.VideoNode, rep: int = 17) -> vs.VideoNode:
    """Multiple denoising stages all done in one function"""
    decs = vdf.noise.decsiz(clip, sigmaS=10, min_in=200 << 8, max_in=240 << 8)
    denoise = haf.SMDegrain(decs, thSAD=200, tr=3, contrasharp=True, RefineMotion=True, pel=4, subpixel=3, prefilter=3)

    efrq = extractFrequency(decs)  # Found out-post encode that I fucked this one up oops thanks flake8  # noqa
    mfrq = mergeFrequency(denoise, denoise)

    mrep = core.rgvs.Repair(mfrq, decs, rep)
    return core.std.MaskedMerge(mrep, decs, mask)


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


def clamp_aa(clip: vs.VideoNode, strength: float = 1.0) -> vs.VideoNode:
    aa_weak = lvf.aa.nneedi3_clamp(clip)
    aa_strong = lvf.aa.upscaled_sraa(clip)
    return lvf.aa.clamp_aa(clip, aa_weak, aa_strong, strength=strength)


def multi_debander(clip: vs.VideoNode, old_clip: vs.VideoNode) -> vs.VideoNode:
    mask = detail_mask(old_clip, brz=(1000, 3500), pf_sigma=False)

    deband = vdf.deband.dumb3kdb(get_y(clip), radius=17, threshold=40)
    deband_chr = placebo_debander(clip, iterations=2, threshold=5, radius=12, grain=4)
    deband = join([deband, plane(deband_chr, 1), plane(deband_chr, 2)])

    return core.std.MaskedMerge(deband, clip, mask)


def grain(clip: vs.VideoNode, **kwargs: Any) -> vs.VideoNode:
    """Consistent grain output across files"""
    from adptvgrnMod import adptvgrnMod

    grain_args: Dict[str, Any] = dict(
        strength=0.35, luma_scaling=10, static=True, size=1.25, sharp=80, grain_chroma=False, seed=42069
    )
    grain_args |= kwargs

    return adptvgrnMod(clip, **grain_args)
