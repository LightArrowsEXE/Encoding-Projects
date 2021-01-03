import ntpath
import os
from functools import partial

import awsmfunc as awsm
import debandshit as dbs
import havsfunc as haf
import kagefunc as kgf
import lvsfunc as lvf
import vapoursynth as vs
import xvs
from finedehalo import fine_dehalo
from vsutil import depth, insert_clip, iterate, join, plane, split

core = vs.core


def keyframes(clip: vs.VideoNode, kf_path: str):
    try:
        os.makedirs("keyframes")
    except:
        pass
    kgf.generate_keyframes(clip, out_path=kf_path)


def deinterlace(clip: vs.VideoNode, TFF: bool, ref: vs.VideoNode = None) -> vs.VideoNode:
    def deint(n, f, clip: vs.VideoNode, nn3: vs.VideoNode) -> vs.VideoNode:
        return nn3 if f.props['_Combed'] > 0 else clip
    vfm = core.vivtc.VFM(clip, order=TFF, clip2=ref)
    nn3 = core.nnedi3cl.NNEDI3CL(clip, True)

    return core.std.FrameEval(vfm, partial(deint, clip=vfm, nn3=nn3), prop_src=vfm)


def debander(clip: vs.VideoNode, **deband_args) -> vs.VideoNode:
    return join([
        core.placebo.Deband(plane(clip, 0), grain=8, **deband_args),
        core.placebo.Deband(plane(clip, 1), grain=0, **deband_args),
        core.placebo.Deband(plane(clip, 2), grain=0, **deband_args)
    ])


# Ranges that get used multiple times
wk_debl_ranges = [(904, 921), (1135, 1159)]
str_debl_ranges = [1665, 1684, (1686, 1694), (1713, 1752)]


src = lvf.src("Fate Project 2020.ts.dgi")[203498:206645]
ivtc = deinterlace(src, TFF=True)
dec = core.std.DeleteFrames(ivtc, range(3, src.num_frames, 5)) \
    .std.AssumeFPS(fpsnum=24000, fpsden=1001)

kf_path = f"keyframes/{ntpath.basename(__file__)[:-4]}_keyframes.txt"
if os.path.isfile(kf_path) is False:
    print("Keyframe file not found; generating")
    keyframes(dec, kf_path)

crop = core.std.CropRel(dec, left=2, right=2, top=2)
ef = awsm.bbmod(crop, left=5, right=6)

planes = split(ef)
debl = lvf.rfs(
    core.deblock.Deblock(planes[0], 20),
    core.deblock.Deblock(planes[0], 28),
    str_debl_ranges)
planes[0] = lvf.rfs(
    debl, core.deblock.Deblock(planes[0], 16),
    wk_debl_ranges)
planes[1], planes[2] = [lvf.rfs(
    core.deblock.Deblock(p, 24),
    core.deblock.Deblock(p, 32),
    str_debl_ranges) for p in planes[1:]]
debl = depth(join(planes), 16)

denoise = haf.SMDegrain(debl, tr=1, thSAD=175, prefilter=3, search=3, contrasharp=True, RefineMotion=True)

ec = haf.EdgeCleaner(denoise, strength=5, rmode=13, hot=True)
dehalo = fine_dehalo(ec, rx=2.4, ry=2.2, brightstr=0.7, darkstr=0)
sharp = haf.LSFmod(dehalo, strength=30, soft=10, edgemode=1, Smethod=2, Lmode=2, defaults='slow', edgemaskHQ=True)
darken = haf.FastLineDarkenMOD(sharp, strength=12)

lmask = kgf.retinex_edgemask(darken)
cwarp = xvs.WarpFixChromaBlend(darken, thresh=112, depth=10)
cwarp = core.std.MaskedMerge(cwarp, darken, lmask)

detail_mask = lvf.denoise.detail_mask(cwarp, sigma=1, brz_a=0.008, brz_b=0.025)
deband_a = dbs.f3kpf(cwarp, range=15, y=20, cb=32)
deband_a = core.std.MaskedMerge(deband_a, cwarp, detail_mask)
deband_b = iterate(cwarp, partial(debander, iterations=3, threshold=8, radius=4), 3)
deband_b = kgf.crossfade(deband_a[2157:], deband_b[2157:], 80)[:81]
deband = insert_clip(deband_a, deband_b, 2157)

grain_a = kgf.adaptive_grain(deband, 0.2, luma_scaling=8)
grain_b = kgf.adaptive_grain(deband, 0.65, luma_scaling=2)
grain_c = kgf.adaptive_grain(deband, 4, luma_scaling=2, static=False)
grain = lvf.rfs(grain_a, grain_b, [(861, 1789), (1957, 2517)])
grain = lvf.rfs(grain, grain_c, [(850, 860)])


out = grain
final = depth(out, 10)
final.set_output()
