import glob
import itertools as it
import ntpath

import havsfunc as haf
import kagefunc as kgf
import lvsfunc as lvf
import vapoursynth as vs
import vardefunc as vdf
import xvs
from finedehalo import fine_dehalo
from vsTAAmbk import TAAmbk
from vsutil import depth, get_y, join, plane

core = vs.core


def dehardsub(clip_a: vs.VideoNode, clip_b: vs.VideoNode,
              signs = [], replace_scenes = [],
              highpass: int = 600, showmask: int = 0) -> vs.VideoNode:
    from functools import partial

    hardsubmask = kgf.hardsubmask(clip_a, clip_b)
    if showmask == 1:
        return hardsubmask
    clip = core.std.MaskedMerge(clip_a, clip_b, hardsubmask)

    if signs:
        hardsubmask_fade = lvf.util.quick_resample(
            clip, partial(
                kgf.hardsubmask_fades, ref=clip_b,
                expand_n=15, highpass=highpass))

        if showmask == 2:
            return hardsubmask_fade

        clip_fade = core.std.MaskedMerge(clip, clip_b, hardsubmask_fade)
        clip = lvf.rfs(clip, clip_fade, ranges=signs)

    if replace_scenes:
        return lvf.rfs(clip, clip_b, ranges=replace_scenes)
    return clip


def placebo_debander(clip: vs.VideoNode, grain: float = 4, **deband_args) -> vs.VideoNode:
    return join([
        core.placebo.Deband(plane(clip, 0), grain=grain, **deband_args),
        core.placebo.Deband(plane(clip, 1), grain=0, **deband_args),
        core.placebo.Deband(plane(clip, 2), grain=0, **deband_args)
    ])


def detail_mask(clip: vs.VideoNode,
                sigma: float = 1.0,
                pf: bool = False
                ) -> vs.VideoNode:
    """
    A detail mask aimed at preserving as much detail as possible
    within darker areas, even if it contains mostly noise.
    """
    clip_y = get_y(clip)
    pf = core.bilateral.Gaussian(clip_y, sigma=1) if pf else clip_y
    ret = core.retinex.MSRCP(pf, sigma=[50, 200, 350], upper_thr=0.005)

    blur = core.bilateral.Gaussian(pf, sigma=sigma)
    blur_diff = core.std.Expr([blur, pf], "x y -").std.Binarize(100)

    blur_ret = core.bilateral.Gaussian(ret, sigma=sigma)
    blur_ret_diff = core.std.Expr([blur_ret, ret], "x y -").std.Binarize(100)

    blurred_mask = core.std.Expr([blur_diff, blur_ret_diff], "x y +")

    kirsch = kgf.kirsch(clip_y).std.Binarize(6000)
    return core.std.Expr([blurred_mask, kirsch], "x y +")


def read_credit_mask(index: int, framerange: str, src_clip: vs.VideoNode) -> tuple:
    # Code for reading a bunch of custom-made lineart masks
    return (framerange, lvf.src(f'assets/{ntpath.basename(__file__)[-6:-4]}/twewy{ntpath.basename(__file__)[-6:-4]}_credit_mask{index}.png', ref=src_clip))



# Args
deband_args = dict(iterations=2, threshold=5, radius=12, grain=4)
nnedi3_args = dict(nsize=3, nns=3, qual=1)
eedi3_args = dict(alpha=0.25, beta=0.5, gamma=40, nrad=2, mdis=20)


# Ranges
credit_ranges = [
    (4858, 4911), (4934, 5004), (5132, 5185), (5190, 5243),
    (5263, 5329), (5335, 5379), (5444, 5518), (5582, 5625),
    (5632, 5716), (5723, 5804), (5834, 5881), (5887, 5953),
    (5981, 6045), (6054, 6094), (6172, 6196), (6340, 6415),
    (6555, 6612), (32119, 32189), (32202, 32273), (32286, 32352),
    (32379, 32462), (32486, 32569), (32653, 32736), (32796, 32879),
    (32892, 32975), (33021, 33104), (33122, 33205), (33228, 33311),
    (33335, 33418), (33438, 33521), (33544, 33627), (33649, 33732),
    (34287, 34333)
]

replace_with_waka = [
    (10, 167)
]

signs_dh = [
    (2395, 2466), (14944, 15066), 22563, (34090, 34102),
    (34152, 34175), (34226, 34249)
]

replace_scenes_dh = [
]



ext = [f'{ntpath.basename(__file__)[-6:-4]}/*.mkv']  # 1 = waka, 2 = Funi
src = [lvf.src(p, force_lsmas=True) for p in it.chain.from_iterable(glob.glob(g) for g in ext)]
b = core.std.BlankClip(src[0], length=1)
src[0] = src[0][0] + src[0] + src[0][-1]
src[1] = src[1][168:]
scomp1 = lvf.comparison.stack_compare(src[0]+b, src[1]+b, make_diff=True)

src = [depth(x, 16) for x in src]

dh = dehardsub(src[0], src[1], signs=signs_dh, replace_scenes=replace_scenes_dh, highpass=2000, showmask=0)
scomp2 = lvf.comparison.stack_compare(dh, src[1], make_diff=True)
#diff = lvf.diff(src[1].bilateral.Gaussian(sigma=2), dh.bilateral.Gaussian(sigma=2), thr=104)  # Comment once used


pf = core.bilateral.Gaussian(get_y(dh), sigma=1.25)
detail_m = detail_mask(pf, pf=True)

denoise = haf.SMDegrain(dh, thSAD=200)
denoise = core.std.MaskedMerge(denoise, dh, detail_m)
decsiz = vdf.decsiz(denoise, sigmaS=4, min_in=208 << 8, max_in=232 << 8)


dehalo = fine_dehalo(decsiz, rx=2, darkstr=0, brightstr=0.9)
aa = core.eedi3m.EEDI3(dehalo, 0, True, sclip=core.nnedi3.nnedi3(dehalo, 0, True, **nnedi3_args), **eedi3_args) \
    .resize.Bicubic(dehalo.width, dehalo.height, src_top=.5)
restore_edges = fine_dehalo(aa, ref=dehalo)


ranged_masks = [read_credit_mask(i, f, restore_edges) for i, f in enumerate(credit_ranges, 1)]

for ranges, mask in ranged_masks:
    mask_credits = core.std.MaskedMerge(restore_edges, denoise, mask)
    restore_edges = lvf.rfs(restore_edges, mask_credits, ranges)


lmask = kgf.retinex_edgemask(restore_edges)
cwarp = xvs.WarpFixChromaBlend(restore_edges, thresh=96, depth=6)
cwarp = core.std.MaskedMerge(cwarp, restore_edges, lmask)

deband = vdf.dumb3kdb(cwarp, threshold=30)
deband = core.std.MaskedMerge(deband, cwarp, detail_m)

grain = kgf.adaptive_grain(deband, 0.2, luma_scaling=4)


out = grain
final = depth(grain, 10)
final[:381].set_output()


if __name__ == '__vapoursynth__':
    import os

    def keyframes(clip: vs.VideoNode, kf_path: str):
        if not os.path.isdir("keyframes"):
            os.makedirs("keyframes")
        kgf.generate_keyframes(clip, out_path=kf_path, header=False)

    kf_path = f"keyframes/{ntpath.basename(__file__)[:-4]}_keyframes.txt"
    if not os.path.isfile(kf_path):
        keyframes(dh[:381], kf_path)
