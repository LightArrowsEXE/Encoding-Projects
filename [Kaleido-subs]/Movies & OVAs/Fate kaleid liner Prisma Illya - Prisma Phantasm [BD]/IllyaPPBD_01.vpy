from functools import partial

import awsmfunc as awsm
import havsfunc as haf
import lvsfunc as lvf
import mvsfunc as mvf
import vapoursynth as vs
import vardefunc as vdf
import zzfunc as zzf
from finedehalo import fine_dehalo
from vsutil import depth, fallback, get_y, join, plane

core = vs.core


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
    placebo_args = dict(iterations=3, threshold=5, radius=16, grain=0)
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
    grain_mask = core.std.Expr(
        [yrangebig, grad_mask, ypw0.std.Binarize(2000).std.Maximum().std.Maximum()], '65535 y - x min z -') \
        .std.BoxBlur(0, 16, 1, 16, 1)

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


# Arguments for debanding, upscaling, etc.
descale_args = dict(threshold=0.002)

opstart = 2789

op_range = [(opstart, opstart+2157)]
ed_range = [(84721, 87043), (89166, 89422)]
descale_range = [(49179, 53688)]


base = r"BDMV/[BDMV][191127] Fate／kaleid liner Prisma☆Illya Prisma☆Phantasm/PRISMAPHANTASM_SP/BDMV/STREAM/"
paths = [fr"{base}00001.m2ts", fr"{base}00004.m2ts"]
src = [lvf.src(p, force_lsmas=True)[24:-24] for p in paths]
src = src[0][24:] + src[1]

src_NCOP = lvf.src(f"{base}00005.m2ts")[24:-24]

credit_mask = vdf.diff_creditless_mask(
    src, src[opstart:opstart+src_NCOP.num_frames-1],
    src_NCOP[:-1], opstart, opstart+src_NCOP.num_frames-1)

ef = awsm.bbmod(src, 2, 2, 1, 1, blur=15, u=False, v=False, scale_thresh=True)
ef = depth(ef, 32)

descale_720 = lvf.scale.descale(ef, height=720, kernel=lvf.kernels.Bicubic(b=0, c=1/2), **descale_args)
descale_810 = lvf.scale.descale(ef, height=810, kernel=lvf.kernels.Spline36(), **descale_args)
scaled = lvf.rfs(descale_720, descale_810, descale_range)
scaled = depth(join([scaled, plane(ef, 1), plane(ef, 2)]), 16)

denoise = haf.SMDegrain(scaled, tr=1, thSAD=50, prefilter=3, search=3, contrasharp=True, RefineMotion=True)
aa = lvf.sraa(denoise, rfactor=1.75, rep=13, downscaler=lvf.kernels.Bicubic().scale, alpha=0.3, beta=0.5, gamma=40)

dehalo_m = fine_dehalo(aa, rx=2, thlimi=72, showmask=1)
edgefix = mvf.BM3D(aa, ref=denoise, sigma=4, psample=0)
edgefix = core.bilateral.Bilateral(edgefix, sigmaS=1, sigmaR=6/255)
dehalo = core.std.MaskedMerge(denoise, edgefix, dehalo_m)

sharp = haf.LSFmod(dehalo, strength=50, soft=10, edgemode=1, Smethod=2, Lmode=2, defaults='slow', edgemaskHQ=True)
sharp = fine_dehalo(sharp, ref=dehalo, rx=3.6)
darken = haf.FastLineDarkenMOD(sharp, strength=12)

merged = core.std.MaskedMerge(darken, depth(ef, 16), depth(credit_mask, 16))
deband = debanding(merged, denoised=True, iterations=2, threshold=4, radius=12)

repl = lvf.rfs(deband, depth(src, 16), ed_range)


out = repl
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
        keyframes(src, kf_path)
