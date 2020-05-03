import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import mvsfunc as mvf
import havsfunc as haf
import descale as ds
import bombzenfunc as bzf
from vsutil import *
from nnedi3_resample import *
from cooldegrain import *
from functools import partial
core = vs.core
core.num_threads = 3


def _rescaler(clip: vs.VideoNode, h: int, b: float, c: float,
              credit_mask: vs.VideoNode = None, 
              src_left: float = 0, src_top: float = 0) -> vs.VideoNode:
    planes = split(clip)
    descaled = core.descale.Debicubic(planes[0], get_w(h, clip.width/clip.height), h, b, c)
    upscaled = nnedi3_resample(descaled, clip.width, clip.height, kernel='gauss', invks=True,
                                invkstaps=2, taps=1, a1=32, nns=4, qual=2, pscrn=4)
    l_mask = fvf.Depth(kgf.retinex_edgemask(fvf.Depth(upscaled, 16)), get_depth(clip))
    if credit_mask is not None:
        l_mask = core.std.Expr([l_mask, credit_mask], "x y -").std.Deflate()
    planes[0] = core.std.MaskedMerge(planes[0], upscaled, l_mask)
    planes[1], planes[2] = [core.resize.Spline36(p, src_left=src_left, src_top=src_top) for p in planes[1:]]
    merged = join(planes)
    if credit_mask is not None:
        return core.std.MaskedMerge(merged, clip, credit_mask)
    return merged


def _create_credit_mask(clip: vs.VideoNode, h: int, b: float, c: float, brz: float = 0.05) -> vs.VideoNode:
    clip_y = get_y(clip)
    descaled = core.fmtc.resample(clip_y, get_w(h), h, kernel='bicubic', a1=b, a2=c, invks=True)
    upscaled = core.fmtc.resample(descaled, clip_y.width, clip_y.height, kernel='bicubic', a1=b, a2=c)
    credit_mask = core.std.Expr([clip_y, upscaled], 'x y - abs').std.Binarize(brz)
    credit_mask = kgf.iterate(credit_mask, core.std.Maximum, 4)
    return kgf.iterate(credit_mask, core.std.Inflate, 2)


hs_signs = """
           [10451 10473] [10483 10509] [10595 10635] [10676 10710] [10853 10978] [11847 11938]
           [20377 20451] [20458 20493] [20536 20558] [21448 21525] [22183 22289] [22404 22511]
           [32165 32365] [23068 23162] [401 485] [2312 2421] [26578 26630] [27095 27146]
           [27540 27623] [29173 29219] [29376 29423] [29520 29567] [29760 29800] [30161 30224]
           [30603 30713] [4423 4468] [4481 4515] [4522 4563] [9034 9072] [9079 9116] [10080 10109]
           [10595 10635] [11976 11989] [3377 3428] [3938 4021] [12772 12789] [12841 12948]
           [13346 13440] [13632 13673] [18932 18939] [22972 23045] [23586 23592] [23651 23656]
           """ # Giving up on doing it in order, just gonna stick it all in there as I find it lol

replace_scenes = None

opstart = 0

src_a = lvf.src(r"02/Kaguya_S2_02_EN_HD.mp4")
src_b = lvf.src(r"02/[HorribleSubs] Kaguya-sama wa Kokurasetai S2 - 02 [1080p].mkv")
src_a = src_a[:11938]+src_a[11937]+src_a[11938:22509]+src_a[22508]+src_a[22509:]+src_a[-1]
src_b = src_b[289:]
scomp = lvf.scomp(src_a, src_b, height=360, make_diff=True)


hardsubmask = kgf.hardsubmask(src_a, src_b)
src = core.std.MaskedMerge(src_a, src_b, hardsubmask)

hardsubmask_fade = fvf.Depth(kgf.hardsubmask_fades(src_a, src_b, highpass=1200), 8)
src_fade = core.std.MaskedMerge(src_a, src_b, hardsubmask_fade)
src = fvf.rfs(src, src_fade, mappings=hs_signs)
if replace_scenes:
    src = fvf.rfs(src, src_b, mappings=replace_scenes)
src = src[:2638]+src[2637]*45+src[2683:] # Freezeframing a sign
scomp2 = lvf.scomp(src, src_b, height=360, make_diff=True)

src = core.std.Limiter(src, 16, [235,240])
src = fvf.Depth(src, 32)


h = 874
b, c =  0, 1
planes = split(src)
planes[0] = ds.Debicubic(planes[0], get_w(h), h, b=b, c=c)

op_filter = fvf.Depth(planes[0], 16)
op_dehalo = haf.FineDehalo(op_filter, rx=2, darkstr=0, brightstr=1.2, contra=1)
op_filter = fvf.Depth(op_dehalo, 32)

planes[0] = nnedi3_resample(op_filter, src.width, src.height, kernel='gauss', invks=True,
                            invkstaps=2, taps=1, a1=32, nns=4, qual=2, pscrn=4)
scaled = join(planes)


denoise = CoolDegrain(scaled, tr=1, thsad=72, thsadc=48, bits=16, blksize=8, overlap=4)
dering = haf.EdgeCleaner(denoise, strength=6, rmode=13, smode=1, hot=True)

credit_mask = _create_credit_mask(src, h, b, c, brz=0.1)
merge = core.std.MaskedMerge(dering, fvf.Depth(src, 16), fvf.Depth(credit_mask, 16))

deband = core.f3kdb.Deband(merge, range=15, y=40, cb=32, cr=32, grainy=36, grainc=0, output_depth=16, keep_tv_range=True)
grain = kgf.adaptive_grain(deband, 0.3, luma_scaling=4)


out = grain
final = fvf.Depth(out, 10)
final.set_output()
