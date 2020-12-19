import os
from functools import partial

import havsfunc as haf
import kagefunc as kgf
import lvsfunc as lvf
import vapoursynth as vs
import xvs
import vardefunc as vdf
from awsmfunc import bbmod
from vsutil import depth, get_y, join, plane

core = vs.core

shader = 'FSRCNNX_x2_56-16-4-1.glsl'
if os.path.exists(shader) is False:
    hookpath = r"mpv\shaders\FSRCNNX_x2_56-16-4-1.glsl"
    shader = os.path.join(os.getenv("APPDATA"), hookpath)


def debander(clip: vs.VideoNode, **deband_args) -> vs.VideoNode:
    return join([
        core.placebo.Deband(plane(clip, 0), grain=6, **deband_args),
        core.placebo.Deband(plane(clip, 1), grain=0, **deband_args),
        core.placebo.Deband(plane(clip, 2), grain=0, **deband_args)
    ])

# Common args
scale_args = dict(height=936, kernel=lvf.kernels.Spline36())
deband_args = dict(iterations=2, threshold=4, radius=14)


src = lvf.src(r"05/[SubsPlease] Majo no Tabitabi - 05 (1080p) [1A8C794D].mkv")[240:]
ef = bbmod(src, left=1, right=1, top=1, bottom=1,
           thresh=100, blur=999, scale_thresh=False,
           y=True, u=True, v=True)
ef = depth(ef, 32)


# Why is the lineart so scuffed
descaled = lvf.scale.descale(ef, upscaler=None, **scale_args)
upscaled = vdf.fsrcnnx_upscale(descaled, ef.width*2, ef.height*2, shader) \
    .resize.Spline36(ef.width, ef.height)
masked = core.std.MaskedMerge(get_y(ef), upscaled,
         lvf.util.quick_resample(ef, kgf.retinex_edgemask).std.Deflate())
scaled = join([masked, plane(ef, 1), plane(ef, 2)])


dering = lvf.util.quick_resample(scaled, partial(haf.HQDeringmod, darkthr=0, sharp=12, mthr=12, thr=24))


# The chroma is completely and utterly fucked
l_mask = lvf.util.quick_resample(dering, kgf.retinex_edgemask).std.Deflate()
cwarp = core.std.MaskedMerge(xvs.WarpFixChromaBlend(dering, depth=16), dering, l_mask)
cwarp = core.rgsf.Repair(cwarp, dering, 13)


# Why is the grain pattern so strong and odd
detail_mask = lvf.denoise.detail_mask(cwarp, brz_a=0.035, brz_b=0.06)
deband = debander(cwarp, **deband_args)
deband = core.std.MaskedMerge(deband, cwarp, detail_mask)

grain = kgf.adaptive_grain(deband, 0.1, luma_scaling=4)


out = grain
final = depth(out, 10)
final.set_output()
