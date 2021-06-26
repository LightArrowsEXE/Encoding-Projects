import os
from functools import partial

import awsmfunc as awsm
import havsfunc as haf
import kagefunc as kgf
import lvsfunc as lvf
import mvsfunc as mvf
import vapoursynth as vs
import vardefunc as vdf
import zzfunc as zzf
from finedehalo import fine_dehalo
from vsTAAmbk import TAAmbk
from vsutil import depth, fallback, get_y, join, plane

core = vs.core


shader = r'FSRCNNX_x2_56-16-4-1.glsl'
if os.path.exists(shader) is False:
    hookpath = r"mpv/shaders/FSRCNNX_x2_56-16-4-1.glsl"
    shader = os.path.join(os.getenv("APPDATA"), hookpath)


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


def transpose_sraa(clip: vs.VideoNode) -> vs.VideoNode:
    sraa_args = dict(rfactor=1.4, rep=13, downscaler=lvf.kernels.Bicubic().scale)

    aa = lvf.sraa(clip.std.Transpose(), **sraa_args)
    return lvf.sraa(aa.std.Transpose(), **sraa_args)


deband_range = [(2025, 2158)]


src = lvf.src(r"E:/src/[BDMV][アニメ]青の祓魔師/[BDMV][アニメ][110622] BlueExorcist 1/BDROM/BDMV/STREAM/00002.m2ts")[24:-49]
ef = awsm.bbmod(src, 3, 3, 3, 3, thresh=4)
ef = lvf.rfs(src, ef, [(1814, 2024)])
ef = depth(ef, 32)

descale = lvf.scale.descale(ef, upscaler=None, kernel=lvf.kernels.Bicubic(b=1/3, c=1/3))
upscaled = vdf.fsrcnnx_upscale(descale, shader_file=shader)
scaled = join([upscaled, plane(ef, 1), plane(ef, 2)])
scaled = depth(scaled, 16)

ref = haf.SMDegrain(scaled, tr=1, thSAD=150, prefilter=3, search=3)
denoise = mvf.BM3D(scaled, sigma=1.4, radius1=1, profile1='lc', psample=0, ref=ref)
denoise = lvf.rfs(scaled, denoise, deband_range)

aa = transpose_sraa(scaled)
aa = lvf.rfs(scaled, aa, [(449, 456)])

str_aa = TAAmbk(aa, aatype='Eedi3SangNom', cycle=12)
str_aa = lvf.rfs(aa, str_aa, [2026])  # lol

dehalo = fine_dehalo(str_aa, rx=1.8)
dehalo = lvf.rfs(str_aa, dehalo, [(425, 433)])

detail_mask = lvf.mask.detail_mask(dehalo, brz_a=0.0075, brz_b=0.0135)
deband_a = debanding(dehalo, iterations=2, threshold=4, radius=14)
deband_b = debanding(dehalo, iterations=3, threshold=6, radius=18)
deband = lvf.rfs(deband_a, deband_b, deband_range)

grain = kgf.adaptive_grain(deband, 0.1, luma_scaling=4)
deband = core.std.MaskedMerge(deband, grain, detail_mask)

grain = kgf.adaptive_grain(deband, 0.25, luma_scaling=4)
grain = lvf.rfs(deband, grain, [(0, 234), (1169, 1810), (2025, 2158)])


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
        keyframes(src, kf_path)
