import os
from functools import partial

import havsfunc as haf
import kagefunc as kgf
import lvsfunc as lvf
import vapoursynth as vs
import vardefunc as vdf
from cooldegrain import CoolDegrain
from finedehalo import fine_dehalo
from vsutil import depth, get_w, get_y, join, plane, split

core = vs.core

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


def reconstruct(clip: vs.VideoNode) -> vs.VideoNode:
    # Reconstruct the chroma to fix how ugly it looks
    def _rescale(clip: vs.VideoNode) -> vs.VideoNode:
        return core.resize.Bicubic(clip, width=1920, height=1080)
    planes = split(clip)
    planes[0] = core.resize.Point(planes[0], planes[1].width, planes[1].height)
    planes = map(_rescale, (planes))
    planes = [core.resize.Bicubic(f, clip.width/2, clip.height/2) for f in planes]
    return join([*planes])


def demangle(clip: vs.VideoNode) -> vs.VideoNode:
    return core.resize.Bicubic(clip, 1920, 1080, src_left=0.5)


def create_mask(clip: vs.VideoNode, height: vs.VideoNode) -> vs.VideoNode:
    downscale = clip.resize.Bicubic(clip.width/2, clip.height/2)
    mask = fine_dehalo(downscale, showmask=1)
    return mask.resize.Bicubic(get_w(height), height)


def debander(clip: vs.VideoNode, **deband_args) -> vs.VideoNode:
    return join([
        core.placebo.Deband(plane(clip, 0), grain=6, **deband_args),
        core.placebo.Deband(plane(clip, 1), grain=0, **deband_args),
        core.placebo.Deband(plane(clip, 2), grain=0, **deband_args)
    ])


# Common args
scale_args = dict(height=828, kernel=lvf.kernels.Bicubic(b=0.262, c=0.369))
deband_args = dict(iterations=2, threshold=3.5, radius=12)


signs = [
    (2031, 2144), (6896, 6925), (7439, 7498), (17723, 17806),
    (19950, 19997), (32245, 32365), (34247, 34255), (34356, 34374)
]

replace = [
]

src_a = lvf.src(r"01/[SubsPlease] Kamisama ni Natta Hi - 01 (1080p) [454F7CDE].mkv")[289:]
src_b = lvf.src(r"01/Kamisama ni Natta Hi - 01 (Wakanim DE 1080p).mkv")
b = core.std.BlankClip(src_a)[0]  # Blank clip to make it easier to scomp it
src_b = src_b[0] + src_b[:17460] + src_b[17459] * 16 + src_b[17460] * 8 + src_b[17465:-73]
scomp = lvf.comparison.stack_compare(src_a+b, src_b+b, make_diff=True)

src = dehardsub(src_b, src_a, signs, replace)
scomp2 = lvf.comparison.stack_compare(src, src_a, make_diff=True)
#diff = lvf.comparison.tvbd_diff(src, src_a, thr=104)

shift = haf.FixChromaBleedingMod(src, cx=-.5, cy=0, thr=100, strength=1, blur=False)
shift = depth(shift, 32)


descaled = lvf.scale.descale(shift, upscaler=None, **scale_args)
upscaled = vdf.fsrcnnx_upscale(descaled, shift.width*2, shift.height*2, shader) \
    .resize.Spline36(shift.width, shift.height)
lmasked = core.std.MaskedMerge(upscaled, get_y(shift),
    depth(create_mask(depth(shift, 16), shift.height), 32))
cmasked = core.std.MaskedMerge(lmasked, get_y(shift),
    lvf.scale.descale(shift, show_mask=True, **scale_args))
recon = demangle(reconstruct(shift)).resize.Bicubic(format=shift.format)
scaled = join([get_y(cmasked), plane(recon, 1), plane(recon, 2)])


denoise = core.std.MaskedMerge(
    lvf.util.quick_resample(scaled, partial(CoolDegrain, tr=1, thsad=72, thsadc=48, bits=16, blksize=8, overlap=4)),
    lvf.util.quick_resample(scaled, partial(CoolDegrain, tr=1, thsad=24, thsadc=48, bits=16, blksize=8, overlap=4)),
    lvf.denoise.adaptive_mask(scaled, luma_scaling=4)
)

aa = lvf.util.quick_resample(
    denoise, partial(lvf.aa.nneedi3_clamp, strength=1.5)
)


detail_mask = lvf.denoise.detail_mask(aa, brz_a=0.035, brz_b=0.06)
deband = debander(aa, **deband_args)
deband = core.std.MaskedMerge(deband, aa, detail_mask)

grain = kgf.adaptive_grain(deband, 0.1, luma_scaling=4)


out = grain
final = depth(out, 10)
final.set_output()
