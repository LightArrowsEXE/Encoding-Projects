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
opstart = 1139
edstart = 31685

# Filtering on specific parts of the OPs
OP_aa  = [(opstart+910, opstart+972), (opstart+1788, opstart+1885)] if opstart is not None else []

# Replace certain scenes in an episodes with an unscaled and un-AA'd clip
replace = []

# AA on scenes with heavy aliasing
aa = []

# Arguments for debanding
deband_args   = dict(iterations = 2, radius = 12)
upscaled_args = dict(width = 1520, height = 855, kernel = lvf.kernels.Bicubic(1/5, 2/5))


src = lvf.src(r"BDMV/[BDMV][191030][Kimetsu no Yaiba][Vol.4]/BDMV/STREAM/00007.m2ts")[:-25]
src = depth(src, 32)

if opstart is not None:
    src_NCOP = lvf.src(r'BDMV/[BDMV][190731][Kimetsu no Yaiba][Vol.1]/BDMV/STREAM/00007.m2ts')[:-24]
    src_NCOP = depth(src_NCOP, 32)

if edstart is not None:
    src_NCED = lvf.src(r'BDMV/[BDMV][190731][Kimetsu no Yaiba][Vol.1]/BDMV/STREAM/00008.m2ts')[:-24]
    src_NCED = depth(src_NCED, 32)


descaled = lvf.scale.descale(get_y(src), mask = None, upscaler = None, **upscaled_args)

# Decently strong dehaloing to fix the leftover halo
dehalo = lvf.util.quick_resample(descaled, fix_lineart)

# Strong AA on specific frames
aa = antialias(dehalo, ranges = OP_aa + aa)

# Upscaling using FSRCNNX and nnedi3_rpow2, then we merge the chroma from ``src``
scaled = reupscale(aa, src)
scaled = lvf.rfs(scaled, src, ranges = replace)


# Masking credits using NCs
op_mask = DCM(src, src[opstart-107:opstart+2050], src_NCOP, opstart-107, opstart+src_NCOP.num_frames-107) if opstart is not None else core.std.BlankClip(scaled)
ed_mask = DCM(src, src[edstart-755:edstart+1402], src_NCED, edstart-755, edstart+src_NCED.num_frames-755) if edstart is not None else core.std.BlankClip(scaled)
credit_mask = core.std.Expr([get_y(op_mask), get_y(ed_mask)], expr = 'x y +')
merge = core.std.MaskedMerge(scaled, src, credit_mask)


detail_mask = lvf.denoise.detail_mask(merge, rad=2, radc=3, brz_a=0.025, brz_b=0.025)
deband = core.placebo.Deband(merge,  planes = 1,   threshold = 4,   grain = 6, **deband_args)
deband = core.placebo.Deband(deband, planes = 2|4, threshold = 5.5, grain = 0, **deband_args)
deband = core.std.MaskedMerge(deband, merge, detail_mask)

grain = kgf.adaptive_grain(deband, 0.25)


out = grain
final = depth(out, 10)
final.set_output()
