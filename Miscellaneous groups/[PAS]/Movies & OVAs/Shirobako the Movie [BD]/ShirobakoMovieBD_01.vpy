import debandshit as dbs
import havsfunc as haf
import kagefunc as kgf
import lvsfunc as lvf
import mvsfunc as mvf
import vapoursynth as vs
from finedehalo import fine_dehalo
from vsutil import depth, get_depth, get_y, insert_clip, join, plane, split

core = vs.core


def transpose_eedi3(clip: vs.VideoNode, **eedi3_args):
    eedi3_args = dict(alpha=0.25, beta=0.5, gamma=40, nrad=2, mdis=20)
    eedi3_args.update(eedi3_args)

    tra = core.std.Transpose(get_y(clip))
    strong = core.eedi3m.EEDI3(tra, 0, True, **eedi3_args)
    strong = core.resize.Spline36(strong, height=clip.width, src_top=0.5)
    strong = core.std.Transpose(strong)
    strong = core.eedi3m.EEDI3(strong, 0, True, **eedi3_args)
    strong = core.resize.Spline36(strong, height=clip.height, src_top=0.5)
    return join([strong, plane(clip, 1), plane(clip, 2)])


def demangle(clip: vs.VideoNode, radius: int = 2) -> vs.VideoNode:
    try:
        from regress import ReconstructMulti, Regress
    except ModuleNotFoundError:
            raise ModuleNotFoundError("demangle: missing dependency 'regress'")

    def dmgl(clip: vs.VideoNode) -> vs.VideoNode:
        args = dict(nsize=1, nns=4, qual=2)
        c = clip.std.Transpose().nnedi3.nnedi3(1, True, **args) \
            .std.Transpose().nnedi3.nnedi3(0, True, **args)
        return c.resize.Bicubic(src_top=.5)

    clipb = depth(clip, 32)
    planes = split(clipb)
    clip_y = planes[0]
    planes[0] = planes[0].resize.Bicubic(planes[1].width, planes[1].height, src_left=-.5,
                                         filter_param_a=1/3, filter_param_b=1/3)
    planes[0], planes[1], planes[2] = map(dmgl, (planes[0], planes[1], planes[2]))
    y_fix = core.std.MakeDiff(clip_y, planes[0])
    yu, yv = Regress(planes[0], planes[1], planes[2], radius=radius)

    u_fix = ReconstructMulti(y_fix, yu, radius=radius)
    planes[1] = core.std.MergeDiff(planes[1], u_fix)
    v_fix = ReconstructMulti(y_fix, yv, radius=radius)
    planes[2] = core.std.MergeDiff(planes[2], v_fix)

    return depth(join([clip_y, planes[1], planes[2]]), get_depth(clip))


def c_mask(clip: vs.VideoNode) -> vs.VideoNode:
    return core.std.Sobel(get_y(clip)).std.Binarize(75 << 8).std.Minimum()


def makemask(clip_y: vs.VideoNode,
             thr: float = (1/10)) -> vs.VideoNode:
    blur = clip_y.std.BoxBlur(hradius=3, vradius=3)
    dark = core.std.Expr([blur, clip_y], 'x y -').std.Binarize(170)
    clean = dark.rgvs.RemoveGrain(3).std.Median()
    dark = core.misc.Hysteresis(clean, dark)
    dev = dark.std.BoxBlur(hradius=8, vradius=8).std.Binarize(65536 * thr)
    return core.std.Expr([dark, dev], 'x y min')


no_den = [(53747, 54514), (54804, 54944), (55440, 55463), (56231, 56605)]
str_deb = [(53374, 53458), (53720, 53746)]

c = dict(left=4, right=4, top=4, bottom=4)


src = lvf.src(r"BDMV/BIXA_1311_1/BDMV/STREAM/00000.m2ts")[:-24]
src = depth(src, 16)

# Specific fixes
src = insert_clip(src, src[56606]*47, 56606)  # F56606 is slighty cleaner than the ones coming after it

ref = haf.SMDegrain(src, tr=1, thSAD=125, prefilter=3, search=3)
denoise = mvf.BM3D(src, sigma=0.45, radius1=1, ref=ref)
denoise = lvf.rfs(denoise, src, no_den)

cfix = demangle(denoise, radius=2)
aa = transpose_eedi3(cfix).rgvs.Repair(cfix, 13)
aa = fine_dehalo(aa, ref=cfix)

detail_mask = core.std.Expr(
    [lvf.denoise.detail_mask(aa, sigma=0.7, brz_a=0.095, brz_b=0.03),
     makemask(plane(aa, 0))], expr="x y + abs")
deband = dbs.f3kpf(aa, range=16, y=33, cb=17)
deband_str = dbs.f3kpf(aa, range=14, y=49, cb=49)
deband_str = lvf.rfs(deband, deband_str, str_deb)
deband = core.std.MaskedMerge(deband, aa, detail_mask)

grain = kgf.adaptive_grain(deband, 0.2, luma_scaling=4)


out = grain
final = depth(out, 10)
final.set_output()


if __name__ == '__vapoursynth__':
    import ntpath
    import os

    def keyframes(clip: vs.VideoNode, kf_path: str):
        if os.path.isdir("keyframes") is False:
            os.makedirs("keyframes")
        kgf.generate_keyframes(clip, out_path=kf_path, header=False)

    kf_path = f"keyframes/{ntpath.basename(__file__)[:-4]}_keyframes.txt"
    if os.path.isfile(kf_path) is False:
        keyframes(src, kf_path)
