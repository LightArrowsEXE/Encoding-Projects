from functools import partial

import debandshit as dbs
import havsfunc as haf
import kagefunc as kgf
import lvsfunc as lvf
import mvsfunc as mvf
import vapoursynth as vs
from finedehalo import fine_dehalo
from vsutil import depth, get_depth, join, plane, split

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
        aa = lvf.aa.nneedi3_clamp(clip, strength=2)

        if str_aa:
            aa = lvf.rfs(aa, lvf.sraa(clip, rfactor=1.2, rep=13,
                                      alpha=0.25, beta=0.5, gamma=40,
                                      nrad=2, mdis=20), str_aa)

        sharp = haf.LSFmod(aa, strength=150, soft=10, edgemode=1, Smethod=2, Lmode=2, defaults='slow', edgemaskHQ=True)
        dh = fine_dehalo(aa, ref=denoise)
        return haf.FastLineDarkenMOD(dh, strength=14)
    else:
        return clip


str_aa = [(27238, 27348), (27721, 27777), (28316, 28447), (29645, 29734)]


src = lvf.src(r"BDMV/[BDMV][201223][Kamisama ni Natta Hi][Vol.01]/BD/BDMV/STREAM/00001.m2ts")[24:-24]
src = depth(src, 16)

descale = lvf.scale.descale(src, height=[828, 832], threshold=0.00225)
descale = depth(descale, 16)

cfix = demangle(descale, radius=1)  # Shame encoding this @444 seems to be broken :(
descale = depth(descale, 16)

ref = haf.SMDegrain(descale, tr=1, thSAD=150, prefilter=3, search=3, contrasharp=True, RefineMotion=True)
denoise = mvf.BM3D(descale, sigma=0.7, radius1=1, profile1='lc', psample=0, ref=ref)

lineart = core.std.FrameEval(denoise, partial(cond_fix_lines, clip=denoise), denoise)
merged = join([lineart, plane(cfix, 1), plane(cfix, 2)])

detail_mask = lvf.denoise.detail_mask(merged, sigma=0.7, brz_a=0.09, brz_b=0.025)
deband = dbs.f3kpf(merged, range=15, y=48, cb=40)
deband = core.std.MaskedMerge(deband, merged, detail_mask)

grain = kgf.adaptive_grain(deband, 0.2, luma_scaling=4)


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
