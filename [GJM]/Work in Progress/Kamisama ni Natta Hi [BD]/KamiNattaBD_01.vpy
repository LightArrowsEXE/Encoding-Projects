from functools import partial

import debandshit as dbs
import havsfunc as haf
import kagefunc as kgf
import lvsfunc as lvf
import mvsfunc as mvf
import vapoursynth as vs
from finedehalo import fine_dehalo
from vsutil import depth, get_depth, get_y, join, plane, split

core = vs.core


def demangle(clip: vs.VideoNode, radius: int = 2) -> vs.VideoNode:
    try:
        from regress import ReconstructMulti, Regress
    except ModuleNotFoundError:
            raise ModuleNotFoundError("demangle: missing dependency 'regress'")

    def dmgl(clip: vs.VideoNode) -> vs.VideoNode:
        return core.resize.Bicubic(clip, 1920, 1080, src_left=.25)

    clipb = depth(clip, 32)
    planes = split(clipb)
    clip_y = planes[0]
    planes[0] = planes[0].resize.Bicubic(planes[1].width, planes[1].height,
        src_left=-.5, filter_param_a=1/3, filter_param_b=1/3)
    planes[0], planes[1], planes[2] = map(dmgl, (planes[0], planes[1], planes[2]))
    y_fix = core.std.MakeDiff(clip_y, planes[0])
    yu, yv = Regress(planes[0], planes[1], planes[2], radius=radius)

    u_fix = ReconstructMulti(y_fix, yu, radius=radius)
    planes[1] = core.std.MergeDiff(planes[1], u_fix)
    v_fix = ReconstructMulti(y_fix, yv, radius=radius)
    planes[2] = core.std.MergeDiff(planes[2], v_fix)

    return depth(join([clip_y, planes[1], planes[2]]), get_depth(clip))


def cond_fix_lines(n, f, clip: vs.VideoFrame) -> vs.VideoFrame:
    if f.props['descaleResolution'] != 1080:
        lmask = core.tcanny.TCanny(clip).std.Inflate()
        aa = lvf.sraa(clip, rfactor=1.3, rep=13, alpha=0.25, beta=0.5, gamma=40, nrad=2, mdis=20)
        aa = core.std.MaskedMerge(clip, aa, lmask)
        return haf.FastLineDarkenMOD(aa, strength=12)
    else:
        return lvf.aa.nneedi3_clamp(clip, strength=2)


def adaptive_grain_mod(clip: vs.VideoNode):
    """
    Yoinked from varde
    """
    try:
        from adptvgrnMod import sizedgrn
    except ModuleNotFoundError:
        raise ModuleNotFoundError("adaptive_grain_mod: missing dependency 'adptvgrnMod'")
    ref = get_y(clip).std.PlaneStats()
    adgmask_a = core.adg.Mask(ref, 30)
    adgmask_b = core.adg.Mask(ref, 12)

    stgrain = sizedgrn(clip, 0.1, 0.05, 1.15, sharp=80)
    stgrain = core.std.MaskedMerge(clip, stgrain, adgmask_b)
    stgrain = core.std.MaskedMerge(clip, stgrain, adgmask_a.std.Invert())

    dygrain = sizedgrn(clip, 0.2, 0.05, 1.5, sharp=80, static=False)
    dygrain = core.std.MaskedMerge(clip, dygrain, adgmask_a)
    return core.std.MergeDiff(dygrain, clip.std.MakeDiff(stgrain))


descale_args = dict(height=[828, 832])


src = lvf.src(r"BDMV/[BDMV][201223][Kamisama ni Natta Hi][Vol.01]/BD/BDMV/STREAM/00000.m2ts")[24:-24]
src = depth(src, 16)

descale = lvf.scale.descale(src, threshold=0.00225, **descale_args)
descale_m = lvf.scale.descale(src, show_mask=True, **descale_args)
descale = depth(descale, 16)

ref = haf.SMDegrain(descale, tr=1, thSAD=150, prefilter=3, search=3, contrasharp=True, RefineMotion=True)
denoise = mvf.BM3D(descale, sigma=0.85, radius1=1, profile1='lc', psample=0, ref=ref)

lineart = core.std.FrameEval(denoise, partial(cond_fix_lines, clip=denoise), denoise)
dehalo = fine_dehalo(lineart, rx=2.2, ry=2, darkstr=0, brightstr=0.7)

merge = core.std.MaskedMerge(dehalo, src, depth(descale_m, 16))
cfix = demangle(merge, radius=2)


detail_mask = lvf.denoise.detail_mask(cfix, sigma=0.8, brz_a=0.09, brz_b=0.025)
deband = dbs.f3kpf(cfix, range=14, y=52, cb=52)
deband = core.std.MaskedMerge(deband, cfix, detail_mask)

grain = adaptive_grain_mod(deband)


out = grain
final = depth(out, 10)
final.set_output()


if __name__ == '__vapoursynth__':
    import ntpath
    import os

    def keyframes(clip: vs.VideoNode, kf_path: str):
        if not os.path.isdir("keyframes"):
            os.makedirs("keyframes")
        kgf.generate_keyframes(clip, out_path=kf_path, header=False)

    kf_path = f"keyframes/{ntpath.basename(__file__)[:-4]}_keyframes.txt"
    if not os.path.isfile(kf_path):
        keyframes(src, kf_path)
