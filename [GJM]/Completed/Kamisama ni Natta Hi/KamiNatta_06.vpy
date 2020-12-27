import ntpath
import os
from functools import partial

import havsfunc as haf
import kagefunc as kgf
import lvsfunc as lvf
import vapoursynth as vs
import vardefunc as vdf
import xvs
from cooldegrain import CoolDegrain
from finedehalo import fine_dehalo
from vsTAAmbk import TAAmbk
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
        core.placebo.Deband(plane(clip, 0), grain=2, **deband_args),
        core.placebo.Deband(plane(clip, 1), grain=0, **deband_args),
        core.placebo.Deband(plane(clip, 2), grain=0, **deband_args)
    ])


def descale(clip: vs.VideoNode, h: int, shader: str, **descale_args):
    descaled = lvf.scale.descale(
        clip, height=h, upscaler=None, **descale_args)
    upscaled = vdf.fsrcnnx_upscale(
        descaled, clip.width, clip.height, shader_file=shader)

    lmasked = core.std.MaskedMerge(get_y(upscaled), get_y(clip),
        depth(create_mask(depth(clip, 16), clip.height), 32))
    cmasked = core.std.MaskedMerge(lmasked, get_y(clip),
        lvf.scale.descale(clip, show_mask=True, **descale_args))

    # This is far from the ideal way to handle the chroma, but it "Works For Now:tm:"
    recon = demangle(reconstruct(clip)).resize.Bicubic(format=clip.format)
    return join([get_y(cmasked), plane(recon, 1), plane(recon, 2)])


# Common args
scale_args = dict(kernel=lvf.kernels.Bicubic(b=0, c=1/2))
deband_a_args = dict(iterations=2, threshold=3.5, radius=14)
deband_b_args = dict(iterations=2, threshold=5, radius=12)


# First frame of OP
opstart = 912

# OP filtering (why does it look so bad sometimes? waka pls)
op_noaa = [(opstart+268, opstart+580)]
op_strongaa = [(opstart, opstart+267)]
op_dehalo = [(opstart+268, opstart+580)]
op_total = [(opstart, opstart+2157)]
op_descale = [(opstart+269, opstart+974)]


# Other scenefiltering (don't expect me to do much)
deband_range = [
]

no_scale = [
]

# Signs and stuff
signs = [
    (3123, 3212)
]

replace = [
]

src_a = lvf.src(r"06/[SubsPlease] Kamisama ni Natta Hi - 06 (1080p) [171AA418].mkv")[289:]
src_b = lvf.src(r"06/TheDayIBecameAGod_06_EN_HD.mp4")
b = core.std.BlankClip(src_a)[0]  # Blank clip to make it easier to scomp it
src_b = src_b[0] + src_b[:-3]
scomp = lvf.comparison.stack_compare(src_a+b, src_b+b, make_diff=True)

src = dehardsub(src_b, src_a, signs, replace)

# Just in case, since I know I'm gonna fuck up next ep and forget xd
if ntpath.basename(__file__) == "KamiNatta_06.vpy":
    # I still hate myself AND frameeval
    fade = kgf.crossfade(src[32195:32264], core.std.BlankClip(src)[:69], 68)
    src = kgf.insert_clip(src, fade + fade[-1] * 102, 32195)


scomp2 = lvf.comparison.stack_compare(src, src_a, make_diff=True)
#diff = lvf.comparison.tvbd_diff(src, src_a, thr=104)


shift = haf.FixChromaBleedingMod(src, cx=-.75, cy=0, thr=100, strength=1, blur=False)
shift = depth(shift, 32)


scaled_828 = descale(shift, h=828, shader=shader, **scale_args)
scaled_832 = descale(shift, h=832, shader=shader, **scale_args)
scaled = lvf.rfs(scaled_828, scaled_832, op_total)


denoise = core.std.MaskedMerge(
    lvf.util.quick_resample(scaled, partial(CoolDegrain, tr=1, thsad=72, thsadc=48, bits=16, blksize=8, overlap=4)),
    lvf.util.quick_resample(scaled, partial(CoolDegrain, tr=1, thsad=24, thsadc=48, bits=16, blksize=8, overlap=4)),
    lvf.denoise.adaptive_mask(scaled, luma_scaling=4)
)

aa = lvf.util.quick_resample(
    denoise, partial(lvf.aa.nneedi3_clamp, strength=2.5)
)
aa = lvf.rfs(aa, denoise, op_noaa)
aa = lvf.rfs(aa, lvf.util.quick_resample(
    denoise, partial(TAAmbk, aatype='Eedi3')), op_strongaa)


ec = lvf.util.quick_resample(
    aa, partial(haf.EdgeCleaner, strength=8, rmode=13)
)

dehalo = lvf.rfs(
    ec, fine_dehalo(ec, rx=2.4, ry=2.2), op_dehalo
) # Starvation results in haloing sometimes, but it still looks much better even then. RIP me, dude.

# Chroma starved in the OP, so forcibly warping it to hopefully wrap it around the lines better
l_mask = lvf.util.quick_resample(dehalo, kgf.retinex_edgemask)
cwarp = core.std.MaskedMerge(xvs.WarpFixChromaBlend(dehalo, depth=8), dehalo, l_mask)
cwarp = lvf.rfs(dehalo, core.rgsf.Repair(cwarp, dehalo, 13), op_total)


detail_mask = lvf.denoise.detail_mask(cwarp, brz_a=0.025, brz_b=0.045)
deband = lvf.rfs(
    debander(cwarp, **deband_a_args),
    debander(cwarp, **deband_b_args),
    deband_range)
deband = core.std.MaskedMerge(deband, cwarp, detail_mask)

grain = kgf.adaptive_grain(deband, 0.15, luma_scaling=2)


out = grain
final = depth(out, 10)
final.set_output()
