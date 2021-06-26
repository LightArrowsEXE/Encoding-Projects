from functools import partial
from typing import Any, Dict, Optional

import awsmfunc as awsm
import havsfunc as haf
import lvsfunc as lvf
import mvsfunc as mvf
import rekt
import vapoursynth as vs
import zzfunc as zzf
from adptvgrnMod import adptvgrnMod
from vsutil import depth, fallback, get_y, iterate, join, plane

core = vs.core


def ivtc(clip: vs.VideoNode, TFF: bool, pattern: int):
    defivtc = core.std.SeparateFields(src, tff=TFF).std.DoubleWeave()
    selectlist = [[0,3,6,8], [0,2,5,8], [0,2,4,7], [2,4,6,9], [1,4,6,8]]
    return core.std.SelectEvery(defivtc, 10, selectlist[pattern % 5])


def mt_xxpand_multi(clip: vs.VideoNode,
                    sw=1, sh=None,
                    mode='square',
                    planes=None, start=0,
                    M__imum=core.std.Maximum,
                    **params) -> vs.VideoNode:
    sh = fallback(sh, sw)
    planes = list(range(clip.format.num_planes)) if planes is None \
        else [planes] if isinstance(planes, int) else planes

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


def debanding(clip: vs.VideoNode, denoised: bool = False, **deband_args) -> vs.VideoNode:
    """
    Written by Zastin, *CAUTIOUSLY* modified by puny little me

    This is all pure black magic to me,
    so I'm just gonna pretend I didn't see anything.
    """
    placebo_args = dict(iterations=2, threshold=4, radius=12, grain=4)
    placebo_args.update(deband_args)

    brz = 256 if denoised else 384

    clip_depth = clip.format.bits_per_sample
    if clip_depth != 16:
        clip = depth(clip, 16)

    clip_y = get_y(clip)
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


def FixEdges(clip, rownum, rowval, colnum, colval, **kwargs):
    bbmod_args = dict(top=3, bottom=3, left=3, right=3, thresh=None, blur=20)
    bbmod_args.update(kwargs)

    fix = rekt.rektlvls(clip, rownum, rowval, colnum, colval)
    return fix.std.MaskedMerge(
        awsm.bbmod(clip, **bbmod_args),
        core.std.Expr([
            fix, rekt.rektlvls(clip, rownum, rowval, colnum, colval, [16, 256])],
            'x y - abs 0 > 65535 0 ?'), 0, True)


def placebo_debander(clip: vs.VideoNode, grain: int = 4, **deband_args) -> vs.VideoNode:
    return join([  # Still not sure why splitting it up into planes is faster, but hey!
        core.placebo.Deband(plane(clip, 0), grain=grain, **deband_args),
        core.placebo.Deband(plane(clip, 1), grain=0, **deband_args),
        core.placebo.Deband(plane(clip, 2), grain=0, **deband_args)
    ])


deband_args = dict(iterations=3, threshold=6, radius=8, grain=12)

ef_val = 20


src = lvf.src(r"BDMV/00078.m2ts")[30:-32]
deint = ivtc(src, TFF=True, pattern=0)[:-4]

edgefix = awsm.bbmod(deint, left=6, right=6, blur=50)
fillborders = core.fb.FillBorders(deint, left=2, right=2, mode="fillmargins")
ef = core.std.Expr([edgefix, fillborders], f'x {ef_val} < y x ?')

crop = core.std.CropRel(ef, left=2, right=2)

bb_post = awsm.bbmod(crop, left=2, right=2)
bb_post = depth(bb_post, 16)


denoise = mvf.BM3D(bb_post, sigma=[1.25, 1])
deband = debanding(denoise, denoised=True)
grain = adptvgrnMod(deband, strength=0.35, size=1.25, sharp=75, luma_scaling=4)


out = grain
final = depth(out, 10)
final.set_output()


if __name__ == '__vapoursynth__':
    import ntpath
    import os

    import kagefunc as kgf

    def keyframes(clip: vs.VideoNode, kf_path: str):
        if not os.path.isdir("keyframes"):
            os.makedirs("keyframes")
        kgf.generate_keyframes(clip, out_path=kf_path, header=False)

    kf_path = f"keyframes/{ntpath.basename(__file__)[:-4]}_keyframes.txt"
    if not os.path.isfile(kf_path):
        keyframes(deint, kf_path)
