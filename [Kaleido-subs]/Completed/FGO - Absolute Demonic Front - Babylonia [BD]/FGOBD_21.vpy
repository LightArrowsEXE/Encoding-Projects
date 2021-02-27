import os
from functools import partial

import kagefunc as kgf
import lvsfunc as lvf
import xvs
from cooldegrain import CoolDegrain
from finedehalo import fine_dehalo
from vardefunc import diff_creditless_mask as DCM
from vsutil import depth, get_w, get_y, join, plane

import vapoursynth as vs

core = vs.core
core.max_cache_size = 1024 * 128
core.num_threads = 40

shader = 'FSRCNNX_x2_56-16-4-1.glsl'
if os.path.exists(shader) is False:
    hookpath = "mpv\shaders\FSRCNNX_x2_56-16-4-1.glsl"
    shader = os.path.join(os.getenv("APPDATA"), hookpath)


def reupscale(clip: vs.VideoNode,
              ref: vs.VideoNode = None,
              width: int = 1920,
              height: int = 1080,
              merge: float = 1 / 2) -> vs.VideoNode:
    """
        Reupscale using FSRCNNX and nnedi3_rpow2 to fix it a bit.
        Code mostly stolen from Varde, but ssshhh. Don't tell him. :)
    """
    fsrcnnx = join([
        clip,
        plane(ref, 1).resize.Bicubic(clip.width, clip.height, clip.format),
        plane(ref, 2).resize.Bicubic(clip.width, clip.height, clip.format)]) \
        .resize.Bicubic(format=vs.YUV444P16)

    fsrcnnx = depth(
        core.placebo.Shader(
            fsrcnnx,
            width=clip.width * 2,
            height=clip.height * 2,
            shader=shader, filter='box'), 32)

    if merge > 0:
        sraa = lvf.sraa(clip, rfactor=1.7, rep=13, height=fsrcnnx.height,
                        downscaler=partial(core.fmtc.resample, kernel='gauss',
                                           invks=True, invkstaps=2,
                                           taps=1, a1=32))
    else:
        sraa = clip.resize.Point(fsrcnnx.width, fsrcnnx.height, fsrcnnx.format)

    merge = core.std.Expr([get_y(fsrcnnx), get_y(sraa)], 'x y < x y ?') \
        .resize.Bicubic(width, height)

    if ref:
        ref = core.resize.Bicubic(ref, width, height, format=vs.YUV444PS) \
            if ref.height > height else ref

    return join([merge, plane(ref, 1), plane(ref, 2)]) \
        if ref is not None else merge


# Common arguments
den_args = dict(tr=1, thsadc=32, bits=16, blksize=4, overlap=2)
deband_args = dict(iterations=2, threshold=4, radius=16)
descale_args = dict(width=get_w(873), height=873,
                    b=0, c=1/2, src_top=0.25,
                    src_width=get_w(872.5), src_height=872.5)
mask_scale_args = dict(width=get_w(873), height=873,
                       kernel=lvf.kernels.Bicubic(0, 1/2),
                       mask=partial(lvf.scale.descale_detail_mask, threshold=0.05),
                       show_mask=True)


# Frames to replace with an unscaled clip
replace = []

# First frame of OP, first frame after preview
opstart = None
edstart = None

src = lvf.src(r"BDMV/[BDMV][ANZX-15513][Fate Grand Order - Absolute Demonic Front Babylonia][Vol.5][JP]/DISC2/BDROM/BDMV/STREAM/00001.m2ts")[24:-24]


if opstart is not None:
    src_NCOP = lvf.src(r'BDMV/[BDMV][ANZX-15510][Fate Grand Order - Absolute Demonic Front Babylonia][Vol.4][JP]/BDROM/DISC2/BDMV/STREAM/00007.m2ts')[24:-24]

if edstart is not None:
    src_NCED = lvf.src(r'BDMV/[BDMV][ANZX-15510][Fate Grand Order - Absolute Demonic Front Babylonia][Vol.4][JP]/BDROM/DISC2/BDMV/STREAM/00008.m2ts')[24:-60]


op_mask = DCM(
    src, src[opstart:opstart+src_NCOP.num_frames-2], src_NCOP,
    opstart, opstart+src_NCOP.num_frames-2) \
    if opstart is not None else core.std.BlankClip(src)
ed_mask = DCM(
    src, src[edstart:edstart+src_NCED.num_frames-3], src_NCED,
    edstart, edstart+src_NCED.num_frames-3) \
    if edstart is not None else core.std.BlankClip(src)
credit_mask = core.std.Expr([get_y(op_mask), get_y(ed_mask)], expr='x y +')
check_mask = core.std.Merge(src, credit_mask.resize.Bicubic(format=src.format))


src = depth(src, 32)
credit_mask = depth(credit_mask, 32)

title_mask = lvf.scale.descale(get_y(src), **mask_scale_args)
descaled = core.descale.Debicubic(get_y(src), **descale_args)
upscaled = reupscale(descaled, src, merge=1/2)

denoise = lvf.util.quick_resample(
    upscaled, partial(CoolDegrain, thsad=24, **den_args)
)

l_mask = lvf.util.quick_resample(denoise, kgf.retinex_edgemask)
aa = lvf.aa.nneedi3_clamp(denoise, strength=1.25)
aa = core.std.MaskedMerge(denoise, aa, l_mask)

dehalo = fine_dehalo(aa, rx=2.4, ry=2.2, darkstr=0, brightstr=1)

# Chroma is slightly misaligned, so we forcibly warp it around the edges
l_mask = lvf.util.quick_resample(dehalo, kgf.retinex_edgemask)
cwarp = core.std.MaskedMerge(xvs.WarpFixChromaBlend(dehalo, depth=6), aa, l_mask)
cwarp = core.rgsf.Repair(cwarp, dehalo, 13)

# Merge credits back and 1080p detail back
masked = core.std.MaskedMerge(cwarp, src, title_mask)
merge = core.std.MaskedMerge(masked, src, credit_mask)
merge = lvf.rfs(merge, src, replace)

detail_mask = lvf.denoise.detail_mask(merge, rad=2, radc=1, brz_a=0.025, brz_b=0.02)
deband = join([
    core.placebo.Deband(plane(merge, 0), grain=8, **deband_args),
    core.placebo.Deband(plane(merge, 1), grain=0, **deband_args),
    core.placebo.Deband(plane(merge, 2), grain=0, **deband_args)
])
deband = core.std.MaskedMerge(deband, merge, detail_mask)

grain = kgf.adaptive_grain(deband, 0.2, luma_scaling=4)


out = grain
final = depth(out, 10)
final.set_output()
