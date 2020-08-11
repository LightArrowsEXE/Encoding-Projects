import os

import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
from vsutil import depth, join, plane, get_y
core = vs.core


shader = 'FSRCNNX_x2_56-16-4-1.glsl'
if os.path.exists(shader) is False:
    hookpath = "mpv/shaders/mpv/shaders/FSRCNNX_x2_56-16-4-1.glsl"
    shader = os.path.join(os.getenv("APPDATA"), hookpath)


str_deband = [(0, 120), (1819, 1845)]
no_deband = [(1789, 1818)]
no_w2x = [(454, 723), (1235, 1267), (1789, 1818), (1846, 2041),
          (2147, 2244), (2371, 2412)]

# Common args
deband_a_args = dict(iterations=2, threshold=4, radius=16)
deband_b_args = dict(iterations=3, threshold=7, radius=16)


src = lvf.src(r"src/output.mkv")
src = core.resize.Bicubic(src, 1920, 1080)
crop = core.std.CropRel(src, bottom=8)
crop = depth(crop, 32)


w2x = core.w2xc.Waifu2x(crop, noise=1, scale=2, block=160)
w2x = core.resize.Bicubic(w2x, crop.width, crop.height)
w2x = lvf.rfs(w2x, crop, no_w2x)

aa = lvf.aa.nneedi3_clamp(w2x, strength=1.5)

detail_mask = lvf.denoise.detail_mask(aa, rad=2, radc=1, brz_a=0.025, brz_b=0.02)
deband_a = join([
    core.placebo.Deband(plane(aa, 0), grain=4, **deband_a_args),
    core.placebo.Deband(plane(aa, 1), grain=0, **deband_a_args),
    core.placebo.Deband(plane(aa, 2), grain=0, **deband_a_args)
])
deband_b = join([
    core.placebo.Deband(plane(aa, 0), grain=4, **deband_b_args),
    core.placebo.Deband(plane(aa, 1), grain=0, **deband_b_args),
    core.placebo.Deband(plane(aa, 2), grain=0, **deband_b_args)
])
deband = lvf.rfs(deband_a, deband_b, str_deband)
deband = core.std.MaskedMerge(deband, aa, detail_mask)
deband = lvf.rfs(deband, aa, no_deband)


grain = kgf.adaptive_grain(deband, 0.25, luma_scaling=4)


out = grain
final = depth(out, 10)
final.set_output()
