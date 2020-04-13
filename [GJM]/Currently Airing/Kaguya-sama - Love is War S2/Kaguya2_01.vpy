import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import mvsfunc as mvf
import havsfunc as haf
from vsutil import *
from nnedi3_resample import *
from cooldegrain import *
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
    credit_mask = kgf.iterate(credit_mask, core.std.Maximum, 6)
    return kgf.iterate(credit_mask, core.std.Inflate, 2)


hs_signs = """
           [130 263] [300 332] [354 428] [1749 1854] [2274 2433] [5922 5930] [5966 5972]
           [6386 6468] 6470 [6478 6527] [8442 8470] [10187 10212] [14404 14497] [14679 14691]
           [16046 16054] [17151 17206] [17515 17563] [17720 17775] [17998 18039] [18977 19198] 
           [19575 19648] [20756 20875] [21224 21354] [21659 21692] [23034 23072] [23672 23766] 
           [24174 24225] [24613 24616] [25081 25084] [25132 25150] [25332 25437] [26837 26840] 
           [26869 26871] [26903 26983] [28618 28653] [29160 29180] [31523 31541] [31734 31805] 
           [31908 31934] [33114 33208] [33717 33720] [33748 33805] [35657 35963]
           """

replace_scenes = """
                 [14290 14402]
                 """

src_a = lvf.src(r"01/Kaguya-Sama Love is War S02E01 [1080p][AAC][JapDub][GerSub][Web-DL].mkv")
src_b = lvf.src(r"01/[Corona-chan] Kaguya-sama Love is War - S02E01 [1080p].mkv")
src_a = src_a[0]*9+src_a[:14386]+src_a[14385]*8+src_a[14386:25062]+src_a[25073:-24]+src_a[-24]*7
src_b = src_b[289:]
scomp = lvf.scomp(src_a, src_b, height=360, make_diff=True)


hardsubmask = kgf.hardsubmask(src_a, src_b)
src = core.std.MaskedMerge(src_a, src_b, hardsubmask)

hardsubmask_fade = fvf.Depth(kgf.hardsubmask_fades(src_a, src_b, highpass=1200), 8)
src_fade = core.std.MaskedMerge(src_a, src_b, hardsubmask_fade)
src = fvf.rfs(src, src_fade, mappings=hs_signs)
if replace_scenes is not None:
    src = fvf.rfs(src, src_b, mappings=replace_scenes)
scomp2 = lvf.scomp(src, src_b, height=360, make_diff=True)

src = fvf.Depth(src, 32)


h = 874
b, c = 1/5, 2/5
scaled = _rescaler(src, h, b, c)
credit_mask = _create_credit_mask(src, h, b, c, brz=0.1)

denoise = CoolDegrain(scaled, tr=1, thsad=72, thsadc=48, bits=16, blksize=8, overlap=4)
dering = haf.EdgeCleaner(denoise, strength=4, rmode=13, smode=1, hot=True)
dehalo = haf.FineDehalo(dering, rx=2.4, thmi=91, thma=191, darkstr=0, brightstr=1.2, contra=1)

merge = core.std.MaskedMerge(dehalo, fvf.Depth(src, 16), fvf.Depth(credit_mask, 16))

deband = core.f3kdb.Deband(merge, range=15, y=40, cb=32, cr=32, grainy=36, grainc=0, output_depth=16)
grain = kgf.adaptive_grain(deband, 0.3, luma_scaling=4)


out = grain
final = fvf.Depth(out, 10)
final.set_output()
