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


opstart          = 0

op_signs         = [(opstart+397,opstart+508)] if opstart is not None else []
hs_signs         = [(2261,2366),(5063,5124),(6693,6781),(6945,6962),
                    (14460,14553),(14567,14672),(14975,15068),(16875,16915),
                    (17421,17636),(22700,22805),(23710,23799),(24601,24634),
                    (25864,25929),(26526,26568),(31625,31779),(32295,32367)]
replace_scenes   = []
op_range         = [(opstart,opstart+2157)]

src_a = lvf.src(r"03/Kaguya_S2_03_EN_HD.mp4")
src_b = lvf.src(r"03/[HorribleSubs] Kaguya-sama wa Kokurasetai S2 - 03 [1080p].mkv")
src_a = src_a[:14672]+src_a[14672]*2+src_a[14673]*24+src_a[14673:]
src_b = src_b[289:]
scomp = lvf.scomp(src_a, src_b)


hardsubmask = kgf.hardsubmask(src_a, src_b)
src = core.std.MaskedMerge(src_a, src_b, hardsubmask)

hardsubmask_fade = fvf.Depth(kgf.hardsubmask_fades(src_a, src_b, highpass=1200), 8)
src_fade = core.std.MaskedMerge(src_a, src_b, hardsubmask_fade)
src = lvf.rfs(src, src_fade, ranges=op_signs + hs_signs)
if replace_scenes:
    src = lvf.rfs(src, src_b, ranges=replace_scenes)
scomp2 = lvf.scomp(src, src_b, height=360, make_diff=True)

src = core.std.Limiter(src, 16, [235,240])
src = fvf.Depth(src, 32)


h = 874
b, c =  0, 0.5
planes = split(src)
descaled = ds.Debicubic(planes[0], get_w(h), h, b=b, c=c)

l_mask = fvf.Depth(kgf.retinex_edgemask(fvf.Depth(descaled, 16)), 32).std.Maximum().std.Inflate()
blur = fvf.Depth(core.bilateral.Bilateral(fvf.Depth(descaled, 16)), 32)
blur = core.std.MaskedMerge(descaled, blur, l_mask)
blur = lvf.rfs(descaled, blur, ranges=op_range)

planes[0] = nnedi3_resample(blur, planes[0].width, planes[0].height, kernel='gauss', invks=True,
                            invkstaps=2, taps=1, a1=32, nns=4, qual=2, pscrn=4)
scaled = join(planes)


denoise = CoolDegrain(scaled, tr=1, thsad=48, thsadc=72, bits=16, blksize=8, overlap=4)
dehalo = haf.FineDehalo(denoise, rx=2, darkstr=0, brightstr=1, contra=1)
dering = haf.EdgeCleaner(dehalo, strength=6, rmode=13, smode=1, hot=True)

credit_mask = _create_credit_mask(src, h, b, c, brz=0.1)
merge = core.std.MaskedMerge(dering, fvf.Depth(src, 16), fvf.Depth(credit_mask, 16))

deband = core.f3kdb.Deband(merge, range=15, y=40, cb=32, cr=32, grainy=36, grainc=0, output_depth=16, keep_tv_range=True)
grain = kgf.adaptive_grain(deband, 0.3, luma_scaling=4)


out = grain
final = fvf.Depth(out, 10)
final.set_output()
