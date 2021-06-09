import glob
import itertools as it
import ntpath

import adptvgrnMod as adp
import havsfunc as haf
import kagefunc as kgf
import lvsfunc as lvf
import vapoursynth as vs
import vardefunc as vdf
import xvs
from finedehalo import fine_dehalo
from vsutil import depth, get_y

core = vs.core


def dehardsub(waka: vs.VideoNode, clean: vs.VideoNode,
              signs = [], replace_scenes = [],
              highpass: int = 600, showmask: int = 0) -> vs.VideoNode:
    from functools import partial

    hardsubmask = kgf.hardsubmask(waka, clean)
    if showmask == 1:
        return hardsubmask
    clip = core.std.MaskedMerge(waka, clean, hardsubmask)

    if signs:
        hardsubmask_fade = lvf.util.quick_resample(
            clip, partial(
                kgf.hardsubmask_fades, ref=clean,
                expand_n=15, highpass=highpass))

        if showmask == 2:
            return hardsubmask_fade

        clip_fade = core.std.MaskedMerge(clip, clean, hardsubmask_fade)
        clip = lvf.rfs(clip, clip_fade, ranges=signs)

    if replace_scenes:
        return lvf.rfs(clip, clean, ranges=replace_scenes)
    return clip


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


# Args
deband_args = dict(iterations=2, threshold=5, radius=12, grain=4)
nnedi3_args = dict(nsize=3, nns=3, qual=1)
eedi3_args = dict(alpha=0.25, beta=0.5, gamma=40, nrad=2, mdis=20)


# OP/ED filtering
opstart = 3693

# Ranges
credit_ranges = [  # Too lazy to really continue this when credits can change every episode.
]  # I'll just handle the credits for BDs.

replace_with_waka = [  # Primarily to prevent super-compressed frames to get dh'd poorly
    (opstart, opstart+2157)
]  # https://slow.pics/c/LSuJnKGM

replace_with_amz = [
]

signs_dh = [
    (5935, 5937), (7133, 7192), (16826, 16903), (21132, 21179),
    (33873, 33886), (33944, 33970), (34040, 34066)
]

replace_scenes_dh = [
]


ext = [f'{ntpath.basename(__file__)[-6:-4]}/*.mkv']  # 0 = amazon, 1 = wakanim, 2 = funi
src = [lvf.src(p, force_lsmas=True) for p in it.chain.from_iterable(glob.glob(g) for g in ext)]
b = core.std.BlankClip(src[0], length=1)
src[1] = src[1][0] + src[1] + src[1][-1]
scomp1 = lvf.comparison.stack_compare(src[1]+b, src[0]+b, make_diff=True)

src = [depth(x, 16) for x in src]

dh = dehardsub(src[1], src[0], signs=signs_dh, replace_scenes=replace_scenes_dh, highpass=2000, showmask=0)
dh = lvf.rfs(dh, src[1], replace_with_waka) if replace_with_waka else dh
dh = lvf.rfs(dh, src[0], replace_with_amz) if replace_with_amz else dh


scomp2 = lvf.comparison.stack_compare(dh, src[0], make_diff=True)
#diff = lvf.diff(src[0].bilateral.Gaussian(sigma=2), dh.bilateral.Gaussian(sigma=2), thr=104)  # Comment once used


# Creating a detail mask using a gaussian blur and edgemasking
pf = core.bilateral.Gaussian(get_y(dh), sigma=1.25)
detail_m = detail_mask(pf, pf=True)

denoise = haf.SMDegrain(dh, thSAD=200)
denoise = core.std.MaskedMerge(denoise, dh, detail_m)
decsiz = vdf.noise.decsiz(denoise, sigmaS=4, min_in=208 << 8, max_in=232 << 8)


dehalo = fine_dehalo(decsiz, rx=2, darkstr=0, brightstr=0.9)
aa = lvf.sraa(dehalo, rfactor=2, rep=17, downscaler=lvf.kernels.Bicubic().scale, opencl=True)
restore_edges = fine_dehalo(aa, ref=dehalo)

aa_wk = lvf.aa.nneedi3_clamp(dehalo, strength=2)

# A very naive approach, but it aims to at least catch the white areas around the credits
# and I'm too lazy to write anything better for now
credit_mask = depth(core.std.Expr(get_y(depth(dh, 8)), expr=f"x 192 > x 255 < and 255 0 ?"), 16)
credits_masked = core.std.MaskedMerge(aa, aa_wk, credit_mask)


lmask = kgf.retinex_edgemask(credits_masked)
cwarp = xvs.WarpFixChromaBlend(credits_masked, thresh=96, depth=6)
cwarp = core.std.MaskedMerge(cwarp, credits_masked, lmask)

deband = vdf.deband.dumb3kdb(cwarp, threshold=40, grain=24)
deband = core.std.MaskedMerge(deband, cwarp, detail_m)

grain = adp.adptvgrnMod(deband, 0.3, size=1.2, static=False, grain_chroma=False, luma_scaling=4)


out = grain
final = depth(grain, 10)
final.set_output()


if __name__ == '__vapoursynth__':
    import os

    def keyframes(clip: vs.VideoNode, kf_path: str):
        if not os.path.isdir("keyframes"):
            os.makedirs("keyframes")
        kgf.generate_keyframes(clip, out_path=kf_path, header=False)

    kf_path = f"keyframes/{ntpath.basename(__file__)[:-4]}_keyframes.txt"
    if not os.path.isfile(kf_path):
        keyframes(dh, kf_path)
