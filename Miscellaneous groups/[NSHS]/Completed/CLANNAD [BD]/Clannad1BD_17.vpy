import os
from functools import partial
from typing import List, Tuple, Union

import havsfunc as haf
import kagefunc as kgf
import lvsfunc as lvf
import mvsfunc as mvf
from awsmfunc import bbmod
from vardefunc import diff_creditless_mask as DCM
from vsTAAmbk import TAAmbk
from vsutil import depth, get_y, insert_clip, join, plane

import vapoursynth as vs

core = vs.core
core.max_cache_size = 1024 * 224
core.num_threads = 12


shader = 'FSRCNNX_x2_56-16-4-1.glsl'
if os.path.exists(shader) is False:
    hookpath = r"mpv/shaders/FSRCNNX_x2_56-16-4-1.glsl"
    shader = os.path.join(os.getenv("APPDATA"), hookpath)


@lvf.misc.chroma_injector
@lvf.misc.allow_variable(width=1920, height=1080)
def tfsr(clip, width: int = 1920, height: int = 1080) -> vs.VideoNode:
    return clip.resize.Point(format=vs.YUV444P16) \
        .placebo.Shader(width=width*2, height=height*2, shader=shader) \
        .resize.Bicubic(width, height, format=clip.format.id)


def fader(clip: vs.VideoNode,
          values: Tuple[int, int, int, int] = None
          ) -> vs.VideoNode:
    """
        A fading function that uses kgf.crossfade to fade given clips.
    """
    for start_frame, end_frame, length, input_frame in values:
        clip = insert_clip(clip, kgf.crossfade(clip[start_frame]
                           * length, clip[end_frame] * length, length - 1),
                           input_frame)
    return clip


def fix_lineart(clip: vs.VideoNode) -> vs.VideoNode:
    """
        A function that performs HQDeringmod with a repair on the lineart.
    """
    dering = lvf.util.quick_resample(
        clip, partial(haf.HQDeringmod, nrmode=1, mrad=2, thr=3, sharp=0)
    )
    return lvf.util.pick_repair(dering)(dering, clip, 13)


def replace_section(clip: vs.VideoNode,
                    width: int, height: int,
                    offset_x: int, offset_y: int,
                    ranges: List[Union[int, Tuple[int, int]]],
                    start: int, offset: int) -> vs.VideoNode:
    """
        Replaces a section in the given clip, using a squaremask.
        It takes a given clip, grabs a single frame
        based off the start and the offset.
        It then replaces parts of the clip using lvf.misc.replace_ranges.
    """
    sqmask = kgf.squaremask(clip, width, height, offset_x, offset_y)
    masked = core.std.MaskedMerge(clip, clip[start-offset], sqmask)
    return lvf.misc.replace_ranges(clip, masked, ranges)


def replace_sqmask(clip_a: vs.VideoNode,
                   clip_b: vs.VideoNode,
                   width: int,
                   height: int,
                   offset_x: int,
                   offset_y: int,
                   ranges: List[Union[int, Tuple[int, int]]]
                   ) -> vs.VideoNode:
    """
        Replaces parts of a given clip's given frame, using a squaremask.
        Squaremasks are used to replace parts of the frame.
    """
    sqmask = kgf.squaremask(clip_a, width, height, offset_x, offset_y)
    masked = core.std.MaskedMerge(clip_a, clip_b, sqmask)
    return lvf.misc.replace_ranges(clip_a, masked, ranges)


# Squaremasks
sqmask = []

# Replace BG Elements
replace_bg = []

# Fix fades with heavy banding
fade_fix = []

# Interpolate specific scenes with shimmering
interp_scene = []

# Replace GER signs with JP Signs
aa_credits = [(4522, 4617), (31779, 31883), (34042, 34171), (34658, 34757)]
JP_signs = [(647, 666), (3641, 3683), (4522, 4617), (18595, 18641), (18801, 18878), (19275, 19327), (21613, 21645), (31779, 31883), (34042, 34171), (34658, 34757)]


# First OP & ED frames
opstart = 1486
edstart = 31884

# Arguments for repeated functions
deband_args = dict(iterations=2, threshold=4, radius=18)
upscaled_args = dict(height=[716, 720], kernel=lvf.kernels.Bilinear())


src_ger = lvf.misc.source(r'BDMV/[BDMV]Clannad/CLANNAD VOLUME 3/BDMV/STREAM/00006.m2ts')[24:-25]
src_jp = lvf.misc.source(r'BDMV/[KUNO-DIY][BDMV][CLANNAD][Blu-ray BOX Disc 1-5 Fin]/CLANNAD_4/BDMV/STREAM/00001.m2ts')[:-48]

if opstart is not None:
    src_NCOP = lvf.src(r'BDMV/[BDMV]Clannad/CLANNAD VOLUME 3/BDMV/STREAM/00013.m2ts')[24:-25]
if edstart is not None:
    src_NCED = lvf.src(r'BDMV/[BDMV]Clannad/CLANNAD VOLUME 3/BDMV/STREAM/00010.m2ts')[24:-25]


# GER BD is overall of higher quality, but replaced quite a few signs
src = lvf.misc.replace_ranges(src_ger, src_jp, ranges=JP_signs)

op_mask = DCM(src, src[opstart:opstart+2154], src_NCOP, opstart, opstart+src_NCOP.num_frames) \
    if opstart is not None else core.std.BlankClip(src)
ed_mask = DCM(src, src[edstart:edstart+2158], src_NCED, edstart, edstart+src_NCED.num_frames) \
    if edstart is not None else core.std.BlankClip(src)
credit_mask = core.std.Expr([get_y(op_mask), get_y(ed_mask)], expr='x y +')
credit_mask = depth(credit_mask, 32)


if sqmask:  # Fix certain frames with other fixes and signs
    for width, height, x, y, ranges in sqmask:
        src = replace_sqmask(src, src_jp, width, height, x, y, ranges)

if replace_bg:  # Fix certain frames with background issues, if applicable.
    for width, height, x, y, ranges, start, offset in replace_bg:
        src = replace_section(src, width, height, x, y, ranges, start, offset)


b = core.std.BlankClip(src)[0]
scomp = lvf.comparison.stack_compare(src_jp+b, src+b, make_diff=True)
ef = bbmod(src, 1, 1, 1, 1, thresh=40, blur=999, y=True, u=False, v=False)
ef = depth(ef, 32)


scaled = lvf.scale.descale(ef, upscaler=lambda clip, width, height:
                           tfsr(ef, clip, width, height), mask=None, **upscaled_args) \
            .rgsf.Repair(ef, 13)


aa = lvf.aa.nneedi3_clamp(scaled)
dering = fix_lineart(aa)


# The credits look fine, but the preview and episode titles are heavily aliased
strong_aa = lvf.misc.replace_ranges(
    ef, lvf.util.quick_resample(ef, partial(TAAmbk, aatype='Eedi3')),
    ranges=aa_credits
)

title_mask = lvf.scale.descale(
    get_y(ef), mask=partial(lvf.scale.descale_detail_mask, threshold=.12),
    show_mask=True, **upscaled_args
)

# We're also masking the credits in the OP/ED by using the NCs as reference
# Masking credits using NCs
merge = core.std.MaskedMerge(dering, strong_aa, title_mask)
merge = core.std.MaskedMerge(merge, ef, credit_mask)


# Interpolation for some scenes with shimmering
if interp_scene:
    interp = lvf.util.quick_resample(
        merge, partial(
            haf.QTGMC, InputType=1, TR0=1, TR1=2, TR2=3, Preset="Very Slow"
        )
    )
    interp = lvf.rfs(merge, interp, ranges=interp_scene)
else:
    interp = merge


# vs-placebo does a pretty aight job of debanding this
detail_mask = lvf.denoise.detail_mask(
    interp, pre_denoise=0.6, brz_a=0.06, brz_b=0.012
)
denoise = mvf.BM3D(interp, sigma=[0.6, 1], profile1='lc')
deband = join([  # For whatever reason this is faster, like ???
            core.placebo.Deband(plane(denoise, 0), grain=10, **deband_args),
            core.placebo.Deband(plane(denoise, 1), grain=0,  **deband_args),
            core.placebo.Deband(plane(denoise, 2), grain=0,  **deband_args)
])
deband = core.std.MaskedMerge(deband, interp, detail_mask)


# Some fades have heavy banding. This fixes that.
fade = fader(deband, values=fade_fix)

grain = kgf.adaptive_grain(fade, 0.45, luma_scaling=4)


out = grain
final = depth(out, 10)
#diff = lvf.comparison.tvbd_diff(src, src_jp, thr=96)
final.set_output()
