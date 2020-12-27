import havsfunc as haf
import kagefunc as kgf
import lvsfunc as lvf
import vapoursynth as vs
from finedehalo import fine_dehalo
from vsutil import depth, join, plane

core = vs.core


def debander(clip: vs.VideoNode, **deband_args) -> vs.VideoNode:
    return join([
        core.placebo.Deband(plane(clip, 0), grain=4, **deband_args),
        core.placebo.Deband(plane(clip, 1), grain=0, **deband_args),
        core.placebo.Deband(plane(clip, 2), grain=0, **deband_args)
    ])


# Common args
deband_args = dict(iterations=2, threshold=3, radius=14)


ep = "08"
src = lvf.src(fr"{ep}/[SubsPlease] Maou-jou de Oyasumi - {ep} (1080p) [3FCA8DD5].mkv")[168:]
src_c = src  # copy for comp purposes
amazon_src = fr"{ep}/Maou-jou de Oyasumi - {ep} (Amazon Prime VBR 1080p).mkv"

# Amazon has better lineart in busy scenes, otherwise similar enough
src_a = lvf.src(amazon_src)
l_mask = kgf.retinex_edgemask(src_a)
src = core.std.MaskedMerge(src, src_a, l_mask)
src = depth(src, 16)


# Relatively lazy and quick script because I want to be able to encode this on my own system for once lol
sharp = haf.LSFmod(src, strength=80, defaults='Slow') # Usually I avoid artificial sharpening like the plague, but meh. It works okay-ish here.
dehalo = fine_dehalo(sharp, rx=2.6, ry=2.4, thmi=80, thma=132, darkstr=0.1, brightstr=0.85)
ec = haf.EdgeCleaner(dehalo, strength=4, rmode=13, hot=True)
ec = depth(ec, 32)  # Lineart is really shit, but I can't figure out the native res. Shit sucks.


detail_mask = lvf.denoise.detail_mask(ec, brz_a=0.02, brz_b=0.025)
deband = debander(ec, **deband_args)
deband = core.std.MaskedMerge(deband, ec, detail_mask)

grain = kgf.adaptive_grain(deband, 0.1, luma_scaling=4)


out = grain
final = depth(out, 10)
final.set_output()
