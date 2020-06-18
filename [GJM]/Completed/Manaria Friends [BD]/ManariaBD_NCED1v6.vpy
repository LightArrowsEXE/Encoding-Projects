from functools import partial
from os import path

import havsfunc as haf
import kagefunc as kgf
import lvsfunc as lvf
from finedehalo import fine_dehalo
from vardefunc import diff_creditless_mask as DCM
from vsutil import depth, get_y, join, plane

import vapoursynth as vs

core                = vs.core
core.max_cache_size = 1024 * 4
core.num_threads    = 14


shader = 'FSRCNNX_x2_56-16-4-1.glsl'
if path.exists(shader) is False:
    shader = r'C:/Users/light/AppData/Roaming/mpv/shaders/FSRCNNX_x2_56-16-4-1.glsl'


def reupscale(clip: vs.VideoNode,
              width: int = 1920,
              height: int = 1080) -> vs.VideoNode:
    """
        Reupscale using FSRCNNX and nnedi3_rpow2 to fix it a bit.
        Code mostly stolen from Varde, but ssshhh. Don't tell him. :)
    """
    args = dict(nsize=4, nns=4, qual=2, pscrn=1)
    nn3 = clip.std.Transpose().nnedi3.nnedi3(0, True, **args) \
           .std.Transpose().nnedi3.nnedi3(0, True, **args)
    nn3 = core.resize.Spline36(nn3, src_top=.5, src_left=.5)

    fsrcnnx = clip.resize.Point(format=vs.YUV444P16, dither_type=None)
    fsrcnnx = depth(core.placebo.Shader(fsrcnnx, width = clip.width * 2, height = clip.height * 2,
                                        shader = shader, filter = 'box'), 32)
    merge = core.std.Merge(nn3, get_y(fsrcnnx), weight=0.5)
    return lvf.util.quick_resample(merge, fix_lineart).resize.Bicubic(width, height)


def fix_lineart(clip) -> vs.VideoNode:
    return fine_dehalo(clip, rx=2.4, ry=2.2, darkstr=0, brightstr=0.8)


# First frame of ED
ed_start = 0

# Very strong AA on some scenes
strong_aa = []

# Replace certain scenes in an episodes with an unscaled clip
replace = []

# Arguments for debanding, upscaling, etc.
deband_args   = dict(iterations = 2, threshold = 4, radius = 12)
upscaled_args = dict(height = 878, kernel = lvf.kernels.Bicubic(b=0, c=1/2))


src = lvf.src(r'BDMV/[BDMV][190402][マナリアフレンズ II]/BD/BDMV/STREAM/00012.m2ts')[1004:1988]
src = depth(src, 32)


descaled = lvf.scale.descale(get_y(src), upscaler = None, **upscaled_args)

# Upscaling using FSRCNNX and nnedi3_rpow2, dehalo/dering, downscale
scaled = reupscale(descaled)
merge = join([scaled, plane(src, 1), plane(src, 2)])


# Debanding and masking, as well as graining
detail_mask = lvf.denoise.detail_mask(merge, pre_denoise=0.2, rad=3, radc=4, brz_a=0.015, brz_b=0.04)
deband = join([ # Twice as fast to process for ??? reason
    core.placebo.Deband(plane(merge, 0), grain = 6, **deband_args),
    core.placebo.Deband(plane(merge, 1), grain = 0, **deband_args),
    core.placebo.Deband(plane(merge, 2), grain = 0, **deband_args)
])
deband = core.std.MaskedMerge(deband, merge, detail_mask)

grain = kgf.adaptive_grain(deband, 0.25)


out = grain
final = depth(out, 10)
final.set_output()
