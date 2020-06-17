from os import path

import fvsfunc as fvf
import havsfunc as haf
import kagefunc as kgf
import lvsfunc as lvf
import mvsfunc as mvf
from awsmfunc import bbmod
from cooldegrain import CoolDegrain
from vsutil import depth, get_y, join, plane

import vapoursynth as vs

core                = vs.core
core.max_cache_size = 1024 * 4
core.num_threads    = 14


shader = 'FSRCNNX_x2_56-16-4-1.glsl'
if path.exists(shader) is False:
    shader = r'C:/Users/light/AppData/Roaming/mpv/shaders/FSRCNNX_x2_56-16-4-1.glsl'


@lvf.misc.chroma_injector
@lvf.misc.allow_variable(width=1920, height=1080)
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
    nn3 = core.resize.Spline36(nn3, clip.width * 2, clip.height * 2,
                               src_top=.5, src_left=.5)

    fsrcnnx = clip.resize.Point(format=vs.YUV444P16, dither_type=None)
    fsrcnnx = core.placebo.Shader(fsrcnnx, width = clip.width * 2, height = clip.height * 2,
                                  shader = shader, filter = 'box').resize.Bicubic(nn3.width, nn3.height,
                                  format=nn3.format)
    merge = core.std.Merge(nn3, fsrcnnx, weight = 1/2)
    return merge.resize.Bicubic(width, height, format=clip.format)


# Arguments for debanding, upscaling, etc.
deband_args = dict(iterations = 2, threshold = 5, radius = 14)


src = lvf.src(r"BDMV/かぐや様は告らせたい Vol.6/BD/BDMV/STREAM/00001.m2ts")[:-26]
ef = bbmod(src, 1, 1, 1, 1, thresh=40, blur=999, y=True, u=False, v=False, scale_thresh=True)
shift = haf.FixChromaBleedingMod(ef, cx=0.25, cy=0, thr=100, strength=1, blur=True)
shift = depth(shift, 32)


scaled = lvf.scale.descale(shift, upscaler = lambda clip, width, height: reupscale(src, clip, width, height), width=1554, height=874)


# Debanding and masking, as well as graining
detail_mask = lvf.denoise.detail_mask(scaled, rad=3, radc=4, brz_a=0.03, brz_b=0.045)
deband = join([ # Twice as fast to process for ??? reason
    core.placebo.Deband(plane(scaled, 0), grain = 8, **deband_args),
    core.placebo.Deband(plane(scaled, 1), grain = 0, **deband_args),
    core.placebo.Deband(plane(scaled, 2), grain = 0, **deband_args)
])
deband = core.std.MaskedMerge(deband, scaled, detail_mask)

grain = kgf.adaptive_grain(deband, 0.25)


out = grain
final = depth(out, 10)
final.set_output()
