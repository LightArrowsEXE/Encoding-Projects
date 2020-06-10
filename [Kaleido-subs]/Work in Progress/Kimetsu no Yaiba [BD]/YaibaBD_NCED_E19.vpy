from functools import partial
from os import path

import havsfunc as haf
import kagefunc as kgf
import lvsfunc as lvf
import mvsfunc as mvf
from finedehalo import fine_dehalo
from vardefunc import diff_creditless_mask as DCM
from vsutil import depth, get_y, join, plane

import vapoursynth as vs

core                = vs.core
core.max_cache_size = 1024 * 3
core.num_threads    = 12


shader = 'FSRCNNX_x2_56-16-4-1.glsl'
if path.exists(shader) is False:
    shader = r'C:/Users/light/AppData/Roaming/mpv/shaders/FSRCNNX_x2_16-0-4-1.glsl'


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
    fsrcnnx = depth(core.placebo.Shader(fsrcnnx, width = clip.width * 2, height = clip.height * 2,
                                        shader = shader, filter = 'box'), 32)
    merge = core.std.Merge(nn3, get_y(fsrcnnx), weight=0.5).resize.Spline36(ref.width, ref.height)
    return join([get_y(merge), plane(ref, 1), plane(ref, 2)])


def fix_lineart(clip) -> vs.VideoNode:
    deh = haf.EdgeCleaner(clip, strength=6, rmode=13, smode=1, hot=True)
    return fine_dehalo(deh, rx=2.2, ry=2, darkstr=0, brightstr=1)


def antialias(clip: vs.VideoNode, ranges = []) -> vs.VideoNode:
    return lvf.rfs(clip, lvf.aa.upscaled_sraa(clip), ranges = ranges)


# Second cut in the OP and blood drop cut in ED
opstart = None
edstart = 293

# Filtering on specific parts of the OPs
OP_aa      = [(opstart+910, opstart+972), (opstart+1788, opstart+1885)] if opstart is not None else []
OP_replace = [(opstart+1594, opstart+1675)] if opstart is not None else []

# Replace certain scenes in an episodes with an unscaled clip
replace = [(edstart, edstart+2156)]

# AA on scenes with heavy aliasing
aa = []

# Arguments for debanding
deband_args   = dict(iterations = 2, radius = 12)
upscaled_args = dict(width = 1520, height = 855, kernel = lvf.kernels.Bicubic(0, 1/2))


src = lvf.src(r"BDMV/[BDMV][200220][Kimetsu no Yaiba][Vol.8]/BDMV/STREAM/00007.m2ts")[24:-26]
src = depth(src, 32)


descaled = lvf.scale.descale(get_y(src), mask = None, upscaler = None, **upscaled_args)

# Amending parts of the lineart that seems slightly halo'd
dehalo = fix_lineart(depth(descaled, 16))

# Strong AA on specific frames
aa = depth(antialias(dehalo, ranges = OP_aa + aa), 32)

# Upscaling using FSRCNNX and muxes in ``src`` chroma
scaled = reupscale(aa, src)
scaled = lvf.rfs(scaled, src, ranges = replace)


detail_mask = lvf.denoise.detail_mask(scaled, rad=2, radc=3, brz_a=0.025, brz_b=0.025)
deband = core.placebo.Deband(scaled, planes = 1,   threshold = 4,   grain = 6, **deband_args)
deband = core.placebo.Deband(deband, planes = 2|4, threshold = 5.5, grain = 0, **deband_args)
deband = core.std.MaskedMerge(deband, scaled, detail_mask)

grain = kgf.adaptive_grain(deband, 0.25)


out = grain
final = depth(out, 10)
final.set_output()
