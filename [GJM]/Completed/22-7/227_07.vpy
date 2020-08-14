from functools import partial

import havsfunc as haf
import kagefunc as kgf
import lvsfunc as lvf
import xvs
from awsmfunc import bbmod
from vsutil import depth, join, plane

import vapoursynth as vs

core = vs.core
core.max_cache_size = 1024 * 128
core.num_threads = 20


def dehardsub(clip_a: vs.VideoNode, clip_b: vs.VideoNode) -> vs.VideoNode:
    hardsubmask = kgf.hardsubmask(clip_a, clip_b)
    clip = core.std.MaskedMerge(clip_a, clip_b, hardsubmask)

    hardsubmask_fade = lvf.util.quick_resample(
        clip_a, partial(kgf.hardsubmask_fades, ref=clip_b, expand_n=15, highpass=600)
    )
    clip_fade = core.std.MaskedMerge(clip_a, clip_b, hardsubmask_fade)
    clip = lvf.rfs(clip, clip_fade, ranges=hs_signs)
    if replace_scenes:
        clip = lvf.rfs(clip, clip_b, ranges=replace_scenes)
    return clip


# Common args
descale_args = dict(height=[872, 873, 900], threshold=0.002)
deband_args = dict(iterations=2, threshold=4, radius=12)


hs_signs = [
    (2828, 2935), (5721, 5783), (7730, 7788),
    (9277, 9409), (34303, 34406)
]

replace_scenes = [

]


src_cr = lvf.src(r"07/[Erai-raws] 22-7 - 07 [1080p][Multiple Subtitle].mkv")
src_wk = lvf.src(r"07/22 7  E07 [1080p][AAC][JapDub][GerSub][Web-DL].mkv")
b = core.std.BlankClip(src_cr)[0]  # Blank clip to make it easier to scomp it
src_wk = src_wk[0] + src_wk + src_wk[-1]*11
scomp = lvf.comparison.stack_compare(src_cr+b, src_wk+b, make_diff=True)

src = dehardsub(src_wk, src_cr)
scomp2 = lvf.comparison.stack_compare(src, src_cr, make_diff=True)
#diff = lvf.comparison.tvbd_diff(src, src_cr, thr=104)

ef = bbmod(src, 1, 1, 1, 1, thresh=50, blur=999,
           y=True, u=False, v=False, scale_thresh=True)
ef = depth(ef, 32)


scaled = lvf.scale.descale(ef, **descale_args)

aa = lvf.aa.nneedi3_clamp(scaled, strength=1.5)
cwarp = xvs.WarpFixChromaBlend(aa, depth=10)
ec = lvf.util.quick_resample(cwarp, partial(
    haf.EdgeCleaner, strength=7, rmode=13, smode=1))


detail_mask = lvf.denoise.detail_mask(ec, rad=2, radc=1, brz_a=0.025, brz_b=0.02)
deband = join([
    core.placebo.Deband(plane(ec, 0), grain=4, **deband_args),
    core.placebo.Deband(plane(ec, 1), grain=0, **deband_args),
    core.placebo.Deband(plane(ec, 2), grain=0, **deband_args)
])
deband = core.std.MaskedMerge(deband, ec, detail_mask)

grain = kgf.adaptive_grain(deband, 0.1, luma_scaling=4)


out = grain
final = depth(out, 10)
final.set_output()
