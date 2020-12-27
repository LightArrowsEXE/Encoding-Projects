import os
from functools import partial

import kagefunc as kgf
import lvsfunc as lvf
import vapoursynth as vs
import vardefunc as vdf
from vsutil import depth, get_y, join, plane
from adjust import Tweak

core = vs.core

"""
    I would just reuse Zastin's script, but I literally can't read it.
    That, and I literally just want this done now.
"""

shader = 'FSRCNNX_x2_56-16-4-1.glsl'
if os.path.exists(shader) is False:
    hookpath = r"mpv\shaders\FSRCNNX_x2_56-16-4-1.glsl"
    shader = os.path.join(os.getenv("APPDATA"), hookpath)


def dehardsub(clip_a: vs.VideoNode, clip_b: vs.VideoNode,
              signs = [], replace_scenes = []) -> vs.VideoNode:
    hardsubmask = kgf.hardsubmask(clip_a, clip_b)
    clip = core.std.MaskedMerge(clip_a, clip_b, hardsubmask)

    hardsubmask_fade = lvf.util.quick_resample(
        clip_a, partial(kgf.hardsubmask_fades, ref=clip_b, expand_n=15, highpass=600)
    )
    clip_fade = core.std.MaskedMerge(clip_a, clip_b, hardsubmask_fade)
    clip = lvf.rfs(clip, clip_fade, ranges=signs)
    return lvf.rfs(clip, clip_b, ranges=replace_scenes)


def debander(clip: vs.VideoNode, **deband_args) -> vs.VideoNode:
    return join([
        core.placebo.Deband(plane(clip, 0), grain=2, **deband_args),
        core.placebo.Deband(plane(clip, 1), grain=0, **deband_args),
        core.placebo.Deband(plane(clip, 2), grain=0, **deband_args)
    ])


# Common args
scale_args = dict(height=864, kernel=lvf.kernels.Lanczos(taps=5))
deband_args = dict(iterations=2, threshold=3, radius=14)


opstart = 1272

signs = [
    (3440, 3548), (5865, 5968), (7327, 7380), (15951, 16094),
    (18588, 18623), (33757, 34046)
]

replace = [
]


src_a = lvf.src(r"src/[HorribleSubs] Uzaki-chan wa Asobitai! - 04 [1080p].mkv")[240:]
src_b = lvf.src(r"src/Uzaki-chan Wants to Hang Out E04 [1080p][AAC][JapDub][GerSub][Web-DL].mkv")
b = core.std.BlankClip(src_a)[0]  # Blank clip to make it easier to scomp it
src_b = src_b[0] + src_b
scomp = lvf.comparison.stack_compare(src_a+b, src_b+b, make_diff=True)

src = dehardsub(src_b, src_a, signs, replace)
scomp2 = lvf.comparison.stack_compare(src, src_a, make_diff=True)
#diff = lvf.comparison.tvbd_diff(src, src_a, thr=104)

cat = lvf.src(r"assets/cat.png", ref=src).resize.Spline36(1920, 150)
cat = core.std.StackVertical([cat, src.std.Crop(top=150)])
src = lvf.rfs(src, cat, [(opstart+2100, opstart+2155)])

src = depth(src, 32)


undim = Tweak(src, cont=1.15, sat=1.15)
undim = lvf.rfs(src, undim, [(11994, 12152)])


descaled = lvf.scale.descale(undim, upscaler=None, **scale_args)
rescaled = vdf.fsrcnnx_upscale(descaled, undim.width, undim.height, shader_file=shader)
c_mask = lvf.scale.descale(undim, show_mask=True, **scale_args)
masked = core.std.MaskedMerge(rescaled, get_y(undim), c_mask)
scaled = join([masked, plane(undim, 1), plane(undim, 2)])


aa = lvf.aa.nneedi3_clamp(scaled, strength=2)

detail_mask = lvf.denoise.detail_mask(aa, brz_a=0.025, brz_b=0.045)
deband = debander(aa, **deband_args)
deband = core.std.MaskedMerge(deband, aa, detail_mask)

grain = kgf.adaptive_grain(deband, 0.15, luma_scaling=2)


out = grain
final = depth(out, 10)
final.set_output()
