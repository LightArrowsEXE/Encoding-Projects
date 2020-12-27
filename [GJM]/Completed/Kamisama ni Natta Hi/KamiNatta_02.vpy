import ntpath
import os
from functools import partial

import havsfunc as haf
import kagefunc as kgf
import lvsfunc as lvf
import vapoursynth as vs
import xvs
from cooldegrain import CoolDegrain
from finedehalo import fine_dehalo
from vsutil import depth, get_w, get_y, join, plane, split

core = vs.core

shader = 'FSRCNNX_x2_56-16-4-1.glsl'
if os.path.exists(shader) is False:
    hookpath = r"mpv\shaders\FSRCNNX_x2_56-16-4-1.glsl"
    shader = os.path.join(os.getenv("APPDATA"), hookpath)


@lvf.misc.chroma_injector
@lvf.misc.allow_variable(width=1920, height=1080)
def tfsr(clip, width: int = 1920, height: int = 1080) -> vs.VideoNode:
    return clip.resize.Point(format=vs.YUV444P16) \
        .placebo.Shader(width=width*2, height=height*2, shader=shader) \
        .resize.Bicubic(width, height, format=clip.format.id)


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
        core.placebo.Deband(plane(clip, 0), grain=2, **deband_args),
        core.placebo.Deband(plane(clip, 1), grain=0, **deband_args),
        core.placebo.Deband(plane(clip, 2), grain=0, **deband_args)
    ])


# Common args
scale_args = dict(height=[828, 832], kernel=lvf.kernels.Bicubic(b=0, c=0.5))
deband_args = dict(iterations=2, threshold=2.5, radius=14)


# First frame of OP
opstart = 0

# OP filtering (why does it look so bad sometimes? waka pls)
op_noaa = [(opstart+268, opstart+580)]
op_dehalo = [(opstart+268, opstart+580)]
op_cwarp = [(opstart, opstart+2157)]

# Signs and stuff
signs = [
    (2536, 2626), (21594, 21705)
]

replace = [
]

src_a = lvf.src(r"02/[SubsPlease] Kamisama ni Natta Hi - 02 (1080p) [1B0A70A9].mkv")[289:]
src_b = lvf.src(r"02/TheDayIBecameAGod_02_EN_HD.mp4")
b = core.std.BlankClip(src_a)[0]  # Blank clip to make it easier to scomp it
src_b = src_a[0] + src_b[:14265] + src_b[14267] * 8 + src_b[14267:-3]
scomp = lvf.comparison.stack_compare(src_a+b, src_b+b, make_diff=True)

src = dehardsub(src_b, src_a, signs, replace)

# Just in case, since I know I'm gonna fuck up next ep and forget xd
if ntpath.basename(__file__) == "KamiNatta_02.vpy":
    src = kgf.insert_clip(src, src[32200] * 168, 32200)

scomp2 = lvf.comparison.stack_compare(src, src_a, make_diff=True)
#diff = lvf.comparison.tvbd_diff(src, src_a, thr=104)


shift = haf.FixChromaBleedingMod(src, cx=-.75, cy=0, thr=100, strength=1, blur=False)
shift = depth(shift, 32)


# This is far from the ideal way to handle the chroma, but it Works For Now:tm:
descaled = lvf.scale.descale(
    shift, upscaler=lambda clip, width, height:
    tfsr(shift, clip, width, height), **scale_args)
lmasked = core.std.MaskedMerge(get_y(descaled), get_y(shift),
    depth(create_mask(depth(shift, 16), shift.height), 32))
cmasked = core.std.MaskedMerge(lmasked, get_y(shift),
    lvf.scale.descale(shift, show_mask=True, **scale_args))
recon = demangle(reconstruct(shift)).resize.Bicubic(format=shift.format)
scaled = join([get_y(cmasked), plane(recon, 1), plane(recon, 2)])
#scaled = lvf.rfs(scaled, shift, op_noscale)

denoise = core.std.MaskedMerge(
    lvf.util.quick_resample(scaled, partial(CoolDegrain, tr=1, thsad=72, thsadc=48, bits=16, blksize=8, overlap=4)),
    lvf.util.quick_resample(scaled, partial(CoolDegrain, tr=1, thsad=24, thsadc=48, bits=16, blksize=8, overlap=4)),
    lvf.denoise.adaptive_mask(scaled, luma_scaling=4)
)

aa = lvf.util.quick_resample(
    denoise, partial(lvf.aa.nneedi3_clamp, strength=2.5)
)
aa = lvf.rfs(aa, denoise, op_noaa)

ec = lvf.util.quick_resample(
    aa, partial(haf.EdgeCleaner, strength=8, rmode=13)
)

dehalo = lvf.rfs(
    ec, fine_dehalo(ec, rx=2.4, ry=2.2), op_dehalo
) # Starvation results in haloing sometimes, but it still looks much better even then. RIP me, dude.

# Chroma starved in the OP, so forcibly warping it to hopefully wrap it around the lines better
l_mask = lvf.util.quick_resample(dehalo, kgf.retinex_edgemask)
cwarp = core.std.MaskedMerge(xvs.WarpFixChromaBlend(dehalo, depth=8), dehalo, l_mask)
cwarp = lvf.rfs(dehalo, core.rgsf.Repair(cwarp, dehalo, 13), op_cwarp)


detail_mask = lvf.denoise.detail_mask(cwarp, brz_a=0.025, brz_b=0.045)
deband = debander(cwarp, **deband_args)
deband = core.std.MaskedMerge(deband, cwarp, detail_mask)

grain = kgf.adaptive_grain(deband, 0.1, luma_scaling=4)


out = grain
final = depth(out, 10)
final.set_output()
