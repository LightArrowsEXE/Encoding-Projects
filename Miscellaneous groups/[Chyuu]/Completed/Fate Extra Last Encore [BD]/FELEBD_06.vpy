import os

import havsfunc as haf
import kagefunc as kgf
import lvsfunc as lvf
import xvs
from finedehalo import fine_dehalo
from vardefunc import diff_creditless_mask as DCM
from vsutil import depth, get_y, join, plane

import vapoursynth as vs

core = vs.core
core.max_cache_size = 1024 * 128
core.num_threads = 20

shader = 'FSRCNNX_x2_56-16-4-1.glsl'
if os.path.exists(shader) is False:
    hookpath = r"mpv\shaders\FSRCNNX_x2_56-16-4-1.glsl"
    shader = os.path.join(os.getenv("APPDATA"), hookpath)


def reupscale(clip: vs.VideoNode, ref: vs.VideoNode,
              width: int = 1920, height: int = 1080) -> vs.VideoNode:
    """
        Reupscale using FSRCNNX and nnedi3_rpow2 to fix it a bit.
        Code mostly stolen from Varde, but ssshhh. Don't tell him. :)
    """
    args = dict(nsize=4, nns=4, qual=2, pscrn=1)
    nn3 = clip.std.Transpose().nnedi3.nnedi3(0, True, **args) \
        .std.Transpose().nnedi3.nnedi3(0, True, **args)
    nn3 = core.resize.Spline36(nn3, src_top=.5, src_left=.5)

    fsrcnnx = clip.resize.Point(format=vs.YUV444P16, dither_type=None)
    fsrcnnx = depth(core.placebo.Shader(fsrcnnx, width=clip.width * 2, height=clip.height * 2,
                                        shader=shader, filter='box'), 32)
    merge = core.std.Merge(nn3, get_y(fsrcnnx), weight=0.5)
    dehalo = lvf.util.quick_resample(merge, fix_lineart).resize.Bicubic(ref.width, ref.height)

    return join([get_y(dehalo), plane(ref, 1), plane(ref, 2)])


def fix_lineart(clip) -> vs.VideoNode:
    deh = haf.EdgeCleaner(clip, strength=5, rmode=13, smode=1, hot=True)
    deh = fine_dehalo(deh, rx=2.4, ry=2.2, darkstr=0, brightstr=1)
    return haf.HQDeringmod(deh, thr=6)


# First black frame of both OP and ED
opstart = 1678
edstart = 31889

# Replace certain scenes with an unscaled and un-AA'd clip
replace = []

# Arguments for debanding, upscaling, etc.
deband_args = dict(iterations=2, threshold=6, radius=14)
upscaled_args = dict(kernel=lvf.kernels.Bicubic(b=0.2620, c=0.3690))


src = lvf.src(r"BDMV/Fate Extra Last Encore/Vol3/BDROM/BDMV/STREAM/00000.m2ts")[24:-24]
src = core.std.Limiter(depth(src, 32), min=0, max=1, planes=0)


if opstart is not None:
    src_NCOP = lvf.src(r'BDMV/Fate Extra Last Encore/Vol1/BDROM/BDMV/STREAM/00011.m2ts')[24:-96]
    src_NCOP = core.std.Limiter(depth(src_NCOP, 32), min=0, max=1, planes=0)


descaled = lvf.scale.descale(get_y(src), upscaler=None, **upscaled_args)

# Upscaling using FSRCNNX and nnedi3_rpow2, dehalo/dering, downscale, then merge the chroma from ``src``
scaled = reupscale(descaled, src)

# The ED is full native 1080p, as well as the titlecard before it, so we replace them with a non-descaled clip here (except Ep1)
scaled = lvf.rfs(scaled, src, ranges=replace + ([(edstart-72, edstart+2158)]) if edstart is not None else [])


# Warping appears to fix up the starved chroma fairly well, so that's what we're doing here
l_mask = lvf.util.quick_resample(scaled, kgf.retinex_edgemask)
cwarp = core.std.MaskedMerge(xvs.WarpFixChromaBlend(scaled, depth=6), scaled, l_mask)
cwarp = core.rgsf.Repair(cwarp, scaled, 13)


# Masking credits in the OP using the NC
op_mask = DCM(src, src[opstart:opstart+2159], src_NCOP, opstart, opstart+src_NCOP.num_frames) if opstart is not None else core.std.BlankClip(src)
merge = core.std.MaskedMerge(cwarp, src, op_mask)


detail_mask = lvf.denoise.detail_mask(merge, rad=3, radc=4, brz_a=0.03, brz_b=0.025)
deband = join([  # Don't ask me why, but for some godforsaken reason this is twice as fast to process
                core.placebo.Deband(plane(merge, 0), grain=6, **deband_args),
                core.placebo.Deband(plane(merge, 1), grain=0, **deband_args),
                core.placebo.Deband(plane(merge, 2), grain=0, **deband_args)
])
deband = core.std.MaskedMerge(deband, merge, detail_mask)

grain = kgf.adaptive_grain(deband, 0.15)


out = grain
final = depth(out, 10)
final.set_output()
