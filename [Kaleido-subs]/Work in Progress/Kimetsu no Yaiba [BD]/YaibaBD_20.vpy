import vapoursynth as vs
import lvsfunc as lvf
import fvsfunc as fvf
import havsfunc as haf
import kagefunc as kgf
import mvsfunc as mvf
from nnedi3_resample import nnedi3_resample
from vsTAAmbk import TAAmbk
from knnfunc import knnAA
from cooldegrain import *
from vsutil import *
core = vs.core


def _rescaler(clip: vs.VideoNode, h: int, b: float, c: float,
              credit_mask: vs.VideoNode = None,
              aa_mappings: str = "") -> vs.VideoNode:
    planes = split(clip)
    descaled = core.descale.Debicubic(planes[0], get_w(h, clip.width/clip.height), h, b, c)
    upscaled = nnedi3_resample(descaled, clip.width, clip.height, kernel='gauss', invks=True,
                                invkstaps=2, taps=1, a1=32, nns=4, qual=2, pscrn=4)
    l_mask = fvf.Depth(kgf.retinex_edgemask(fvf.Depth(upscaled, 16)), get_depth(clip))
    if credit_mask is not None:
        l_mask = core.std.Expr([l_mask, credit_mask], "x y -").std.Deflate()
    planes[0] = core.std.MaskedMerge(planes[0], upscaled, l_mask)
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


def _fix_lineart(clip) -> vs.VideoNode:
    dehalo = haf.FineDehalo(clip, rx=2.4, thmi=91, thma=191, darkstr=0, brightstr=1.2, contra=1)
    dering = haf.EdgeCleaner(dehalo, strength=4, rmode=13, smode=1, hot=True)
    return core.rgvs.Repair(dering, clip, 13)


def _create_dmask(clip: vs.VideoNode, luma_scaling: float, depth: Optional[int] = None) -> vs.VideoNode:
    if depth:
        clip = fvf.Depth(clip, depth)
    return core.adg.Mask(clip.std.PlaneStats(), luma_scaling)


def _adap_denoise(clip: vs.VideoNode, luma_scaling: float, depth: int) -> vs.VideoNode:
    denoise_a = CoolDegrain(clip, tr=1, thsad=72, thsadc=48, bits=depth, blksize=8, overlap=4)
    denoise_b = CoolDegrain(clip, tr=1, thsad=24, thsadc=48, bits=depth, blksize=8, overlap=4)
    return core.std.MaskedMerge(denoise_a, denoise_b, _create_dmask(clip, luma_scaling, depth))


def _adap_deband(clip: vs.VideoNode, luma_scaling: float, mappings: str = "") -> vs.VideoNode:
    deband_bright = core.f3kdb.Deband(clip, range=20, y=32, cb=48, cr=48, grainy=24, grainc=0, output_depth=16)
    deband_darker = core.f3kdb.Deband(clip, range=18, y=40, cb=56, cr=56, grainy=24, grainc=0, output_depth=16)
    merged = core.std.MaskedMerge(deband_bright, deband_darker, _create_dmask(clip, luma_scaling))
    return fvf.rfs(merged, deband_darker, mappings)


def _w2x(clip: vs.VideoNode, mappings: str) -> vs.VideoNode:
    depth = get_depth(clip)
    if depth != 32:
        clip = fvf.Depth(clip, 32)
    w2x = core.caffe.Waifu2x(clip, noise=3, scale=1, model=6, cudnn=True, processor=0, tta=False)
    w2x = fvf.rfs(clip, w2x, mappings)
    return fvf.Depth(w2x, depth)


def _grain(clip: vs.VideoNode, mappings_weak: str, mappings_strong: str) -> vs.VideoNode:
    grain_a = kgf.adaptive_grain(clip, 0.25, luma_scaling=8)
    grain_b = kgf.adaptive_grain(clip, 1.4, luma_scaling=4, static=False)
    grain_c = kgf.adaptive_grain(clip, 4, luma_scaling=4, static=False)
    grain = fvf.rfs(grain_a, grain_b, mappings_weak)
    return fvf.rfs(grain, grain_c, mappings_strong)


def _interp(clip: vs.VideoNode, strength: float, mappings: str) -> vs.VideoNode:
    l_mask = kgf.retinex_edgemask(clip).std.Maximum()
    b_mask = core.std.Binarize(get_y(clip), 0.3).std.Invert()
    mask = core.std.Expr([l_mask, b_mask], "x y -").std.Maximum().std.Inflate()

    aa = TAAmbk(clip, aatype='Eedi3', mclip=mask, cycle=1)
    aa = core.std.MaskedMerge(aa, haf.QTGMC(aa, InputType=1, TR2=3), mask)
    return fvf.rfs(clip, aa, mappings=mappings)


opstart = 707 # Second cut in the OP

OP_w2x =            f"{opstart+1483} {opstart+1484}" if opstart is not None else ""
OP_interp =         f"[{opstart+185} {opstart+290}] [{opstart+1555} {opstart+1593}]" if opstart is not None else ""
OP_aa =             f"[{opstart+910} {opstart+972}] [{opstart+1788} {opstart+1885}]" if opstart is not None else ""
OP_deband =         f"[{opstart+1021} {opstart+1186}]" if opstart is not None else ""

OP_grain_weak =     f"[{opstart+1053} {opstart+1208}] [{opstart+1897} {opstart+1939}] [{opstart+1997} {opstart+2050}]" if opstart is not None else ""
OP_grain_strong =   f"[{opstart-80} {opstart+181}] [{opstart+294} {opstart+301}] [{opstart+1209} {opstart+1291}]" if opstart is not None else ""


# Darker, more cinematic close-up shots or with black backgrounds + white glow
cinematics =    """
                [366 413] [462 491]
                [2950 2997] [3616 3826]
                [4720 4732]
                [7208 7279]
                [26956 26967] [27100 27111] [27124 27131]
                """

# Awful webs with heavy aliasing
webs =          """
                [6452 6665] [6736 6875] [8035 8271] [8405 8451]
                [10003 10214] [10329 10734] [10889 10960] [11554 11751]
                [11812 11964] [22374 22496] [25304 25459] [25641 25719]
                [27746 28118] [29614 29806]
                """

heavy_bands =   "[25566 25719]"


src = lvf.src(r"BDMV/[BDMV][200325][Kimetsu no Yaiba][Vol.9]/BDMV/STREAM/00004.m2ts")
src = src[:-26]
src = core.std.Expr(src, "x 16 max 235 min")
src = fvf.Depth(src, 32)


h = 855
b, c = 1/5, 2/5
credit_mask = _create_credit_mask(src, h, b, c, brz=0.10)
scaled = _rescaler(src, h, b, c, aa_mappings=OP_aa + cinematics + webs)

denoise_a = _adap_denoise(scaled, luma_scaling=8, depth=16)
denoise_b = mvf.BM3D(scaled, sigma=[2,3.5], depth=16, profile1='lc')
denoise = fvf.rfs(denoise_a, denoise_b, mappings=heavy_bands)

w2x = _w2x(denoise, mappings=OP_w2x)

dehalo = _fix_lineart(w2x)
interp = _interp(dehalo, strength=1.7, mappings=OP_interp)

merge = core.std.MaskedMerge(interp, fvf.Depth(src, 16), fvf.Depth(credit_mask, 16))

deband_a = _adap_deband(merge, luma_scaling=4, mappings=OP_deband)
deband_b = core.f3kdb.Deband(merge, range=5, y=72, cb=80, cr=80, grainy=0, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(deband_b, range=14, y=64, cb=72, cr=72, grainy=48, grainc=0, output_depth=16)
deband = fvf.rfs(deband_a, deband_b, mappings=heavy_bands)

grain_a = _grain(deband, OP_grain_weak, OP_grain_strong)
grain_b = core.grain.Add(deband, var=3, uvar=0, constant=False)
grain_c = kgf.adaptive_grain(deband, 0.7, luma_scaling=4)
grain = fvf.rfs(grain_a, grain_b, mappings=cinematics)
grain = fvf.rfs(grain, grain_c, mappings=heavy_bands)


out = grain
final = fvf.Depth(out, 10)
final.set_output()
