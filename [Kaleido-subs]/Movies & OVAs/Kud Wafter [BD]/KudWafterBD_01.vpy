import debandshit as dbs
import havsfunc as haf
import kagefunc as kgf
import lvsfunc as lvf
import mvsfunc as mvf
import rekt
import vapoursynth as vs
from finedehalo import fine_dehalo
from vsTAAmbk import TAAmbk
from vsutil import depth, get_y, join, plane, scale_value

core = vs.core


def makemask(clip_y: vs.VideoNode,
             thr: float = (1/10)) -> vs.VideoNode:
    blur = clip_y.std.BoxBlur(hradius=3, vradius=3)
    dark = core.std.Expr([blur, clip_y], 'x y -').std.Binarize(170)
    clean = dark.rgvs.RemoveGrain(3).std.Median()
    dark = core.misc.Hysteresis(clean, dark)
    dev = dark.std.BoxBlur(hradius=8, vradius=8).std.Binarize(65536 * thr)
    return core.std.Expr([dark, dev], 'x y min')


def interpolator(clip: vs.VideoNode, ranges=[]) -> vs.VideoNode:
    l_mask = kgf.retinex_edgemask(clip)
    interp = haf.QTGMC(clip, InputType=1, TR0=2, TR1=2, TR2=1, Preset="Placebo", RepChroma=False)
    interp = core.std.MaskedMerge(clip, interp, l_mask)
    return lvf.rfs(clip, interp, ranges = ranges)


# Common args
deband_args = dict(iterations=1, threshold=2, radius=12)
sraa_args = dict(rfactor=1.5, alpha=0.6, beta=0.2, gamma=10, nrad=3)
sharpen_args = dict(strength=70, soft=10, edgemode=1, Smethod=2, Lmode=2, defaults='slow', edgemaskHQ=True)


# Scenefiltering
outro = [(65304, 73199)]
interp_range = [(19742, 19788), (28681, 28774), (29420, 29538), (30591, 30619)]

weak_aa = [(966, 1000)]
str_aa = [(0, 124), (857, 894), (1105, 1235), (1301, 1367), (5664, 6001), (6959, 7143), (19742, 19788)]
sprstr_aa = [(23358, 23398)]
str_sharp = [(2765, 2845)]
str_deband = [(23156, 23310)]


src = [lvf.src(r"BDMV/AKUDWAFTER/BDMV/STREAM/00002.m2ts"), lvf.src(r"BDMV/AKUDWAFTER/BDMV/STREAM/00003.m2ts")]
src = [depth(x, 16) for x in src]
avg = core.average.Mean(src, preset=3)
avg = lvf.rfs(avg, src[0], outro)[24:-24]

# Parts of this script are inspired by or taken from Varde's script. Thanks!
ref = haf.SMDegrain(avg, tr=1, thSAD=75, prefilter=3, search=3, contrasharp=True, RefineMotion=True)
denoise = mvf.BM3D(avg, sigma=[0.55, 0.65], radius1=1, profile1='lc', psample=0, ref=ref)


aa_weak = lvf.aa.nneedi3_clamp(denoise, strength=1.6)
aa_str = TAAmbk(denoise, aatype='Eedi3')
aa_sprstr = rekt.rekt_fast(denoise, lambda c: lvf.sraa(c, **sraa_args), left=750, right=580, top=950)
aa = lvf.rfs(aa_weak, aa_str, str_aa)
aa = lvf.rfs(aa, aa_sprstr, sprstr_aa)

interp = interpolator(aa, interp_range)


sharp = haf.LSFmod(get_y(interp), **sharpen_args)
lmask = core.std.Sobel(get_y(interp)).std.Binarize(75 << 8).std.Minimum()
sharp = core.std.MaskedMerge(get_y(interp), sharp, lmask)
dehalo = fine_dehalo(sharp, ref=get_y(interp))
darken = haf.FastLineDarkenMOD(dehalo, strength=14)
darken = join([darken, plane(interp, 1), plane(interp, 2)])


diff_den = mvf.BM3D(darken, sigma=[2,0], profile1='lc')
diff_clip = core.std.MakeDiff(darken, diff_den)

detail_mask = core.std.Expr(
    [lvf.denoise.detail_mask(darken,
     sigma=0.4, brz_a=0.0095, brz_b=0.065),
     makemask(get_y(darken)),
     lmask], expr="x y + z + abs")
deband_wk = dbs.f3kpf(diff_den, range=18, y=32, cb=32)
deband_st = dbs.f3kpf(diff_den, range=18, y=64, cb=64)
deband = lvf.rfs(deband_wk, deband_st, str_deband)
deband = core.std.MaskedMerge(deband, diff_den, detail_mask)
diff_rev = core.std.MergeDiff(deband, diff_clip)

grain = kgf.adaptive_grain(diff_rev, 0.25, luma_scaling=4)


out = grain
final = depth(out, 10)
final.set_output()
