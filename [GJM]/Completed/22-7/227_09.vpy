import os
from functools import partial

import havsfunc as haf
import kagefunc as kgf
import lvsfunc as lvf
import vardefunc as vdf
import xvs
from awsmfunc import bbmod
from finedehalo import fine_dehalo
from vsutil import depth, join, plane

import vapoursynth as vs

core = vs.core
core.max_cache_size = 1024 * 128
core.num_threads = 20


shader = 'FSRCNNX_x2_56-16-4-1.glsl'
if os.path.exists(shader) is False:
    hookpath = r"mpv\shaders\FSRCNNX_x2_56-16-4-1.glsl"
    shader = os.path.join(os.getenv("APPDATA"), hookpath)


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


def reupscale(clip: vs.VideoNode, ref:vs.VideoNode,
              shader: str) -> vs.VideoNode:
    def _rescale(clip, n, f):
        return vdf.fsrcnnx_upscale(
            clip.resize.Bicubic(f.width, f.height),
            1080, shader, core.resize.Bicubic)
    upscaled = core.std.FrameEval(clip, partial(_rescale, clip=clip),
                                  prop_src=clip) \
        .resize.Bicubic(ref.width, ref.height)
    return join([upscaled, plane(ref, 1), plane(ref, 2)])


# Common args
descale_args = dict(height=[872, 873, 900], threshold=0.002)
deband_args = dict(iterations=2, threshold=4, radius=12)


hs_signs = [
    (4579, 4678), (6898, 6987), (7756, 7911), (12190, 12284),
    (18498, 18550), (31674, 31677), (31732, 31735), (31789, 31792)
    (34264, 34310)
]

replace_scenes = [

]


src_cr = lvf.src(r"09/[Erai-raws] 22-7 - 09 [1080p][Multiple Subtitle].mkv")
src_wk = lvf.src(r"09/22 7  E09 [1080p][AAC][JapDub][GerSub][Web-DL].mkv")
b = core.std.BlankClip(src_cr)[0]  # Blank clip to make it easier to scomp it
src_wk = src_wk[0] + src_wk[:15930] + src_wk[15930] * 13 + src_cr[15944:16016] + src_wk[15974:34269] + src_cr[34311:]
scomp = lvf.comparison.stack_compare(src_cr+b, src_wk+b, make_diff=True)

src = dehardsub(src_wk, src_cr)
scomp2 = lvf.comparison.stack_compare(src, src_cr, make_diff=True)
#diff = lvf.comparison.tvbd_diff(src, src_cr, thr=104)

ef = bbmod(src, 1, 1, 1, 1, thresh=50, blur=999,
           y=True, u=False, v=False, scale_thresh=True)
ef = depth(ef, 32)


credit_mask = lvf.scale.descale(ef, show_mask=True, **descale_args)
descaled = lvf.scale.descale(ef, upscaler=None, **descale_args)
upscaled = reupscale(descaled, ef, shader)
scaled = core.std.MaskedMerge(upscaled, ef, credit_mask)

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
