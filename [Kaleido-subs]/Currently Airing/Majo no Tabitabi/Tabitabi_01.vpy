from functools import partial

import fvsfunc as fvf
import havsfunc as haf
import kagefunc as kgf
import lvsfunc as lvf
import xvs
import vapoursynth as vs
from awsmfunc import bbmod
from finedehalo import fine_dehalo
from vsutil import depth, join, plane

core = vs.core


def debander(clip: vs.VideoNode, **deband_args) -> vs.VideoNode:
    return join([
        core.placebo.Deband(plane(clip, 0), grain=6, **deband_args),
        core.placebo.Deband(plane(clip, 1), grain=0, **deband_args),
        core.placebo.Deband(plane(clip, 2), grain=0, **deband_args)
    ])

# Common args
deband_args = dict(iterations=2, threshold=4, radius=14)


src_a = lvf.src(r"01/Majo no Tabitabi - 01 (BS11).ts.dgi")[1320:48073]
src_b = lvf.src(r"01/Majo no Tabitabi - 01 (AbemaTV 1080p).mkv") # for matching + removing some stuff

src = fvf.JIVTC(src_a, 1, thr=15)[:2422] \
    + fvf.JIVTC(src_a, 0, thr=15)[3860:15129] \
    + fvf.JIVTC(src_a, 0, thr=15)[16567:]

# Masking. Would mask away the logo and stuff, but colours are too noticeably different in darker areas.
sqmask = kgf.squaremask(src, 1044, 51, 439, 949)

warning_masked = core.std.MaskedMerge(src, src_b, sqmask)
masked = lvf.rfs(src, warning_masked, [(2686, 2923)])
masked = lvf.rfs(masked, src_b, [(14498, 14526), (15762, 15820), (16044, 16098), (16902, 17394), (26768, 26889)])


crop = core.std.CropRel(masked, left=2, right=2)
ef = bbmod(crop, left=4, right=4, top=1, bottom=1,
           thresh=100, blur=999, scale_thresh=False,
           y=True, u=True, v=True)
ef = depth(ef, 16)


debl = fvf.AutoDeblock(ef)
ec = haf.EdgeCleaner(debl, strength=8, rmode=13, hot=True)
dehalo = fine_dehalo(ec, rx=2.4, ry=2.2, darkstr=0.1, brightstr=1)
dehalo = depth(dehalo, 32)

l_mask = lvf.util.quick_resample(dehalo, kgf.retinex_edgemask)
cwarp = core.std.MaskedMerge(xvs.WarpFixChromaBlend(dehalo, depth=16), dehalo, l_mask)
cwarp = core.rgsf.Repair(cwarp, dehalo, 13)


detail_mask = lvf.denoise.detail_mask(cwarp, brz_a=0.08, brz_b=0.08)
deband = debander(cwarp, **deband_args)
deband = core.std.MaskedMerge(deband, cwarp, detail_mask)

grain = kgf.adaptive_grain(deband, 0.1, luma_scaling=4)


t1 = lvf.src(r"Tabitabi_01v2_01 (Premux).mkv")
t2 = lvf.src(r"Tabitabi_01v2_02 (Premux).mkv")

out = grain
final = depth(out, 10)
final[t1.num_frames:-t2.num_frames].set_output()
