import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import mvsfunc as mvf
import havsfunc as haf
from vsutil import *
from cooldegrain import *
core = vs.core
core.num_threads = 3


def _fractional_descale(clip: vs.VideoNode, h: int, b: float, c: float, src_left: float = None) -> vs.VideoNode:
    planes = split(clip)
    planes[0] = core.fmtc.resample(planes[0], get_w(h), h, sy=math_l, kernel='bicubic', a1=b, a2=c, invks=True)
    planes[0] = lvf.upscaled_sraa(planes[0], h=clip.height, rfactor=2.4, sharp_downscale=True)
    planes[0] = core.resize.Spline36(planes[0], src_top=-math_l)
    if src_left:
        planes[1], planes[2] = [core.resize.Bicubic(p, src_left=src_left) for p in planes[1:]]
    return join(planes)


def _create_credit_mask(clip: vs.VideoNode, h: int, b: float, c: float) -> vs.VideoNode:
    clip_y = get_y(clip)
    descaled = core.fmtc.resample(clip_y, get_w(h), h, sy=math_l, kernel='bicubic', a1=b, a2=c, invks=True)
    upscaled = core.fmtc.resample(descaled, clip_y.width, clip_y.height, sy=-math_l, kernel='bicubic', a1=b, a2=c)
    credit_mask = core.std.Expr([clip_y, upscaled], 'x y - abs').std.Binarize(10000)
    credit_mask = kgf.iterate(credit_mask, core.std.Maximum, 6)
    return kgf.iterate(credit_mask, core.std.Inflate, 2)


def _fix_lineart(clip) -> vs.VideoNode:
    dehalo = haf.FineDehalo(clip, rx=2.3, thmi=91, thma=191, darkstr=0, brightstr=1.6, contra=1)
    dering = haf.EdgeCleaner(dehalo, strength=6, rmode=13, smode=1, hot=True)
    return core.rgvs.Repair(dering, clip, 13)


def _create_dmask(clip: vs.VideoNode, luma_scaling: float, depth: int) -> vs.VideoNode:
    if depth:
        clip = fvf.Depth(clip, depth)
    return core.adg.Mask(clip.std.PlaneStats(), luma_scaling)


def _adap_denoise(clip: vs.VideoNode, luma_scaling: float, depth: int) -> vs.VideoNode:
    d_mask = _create_dmask(clip, luma_scaling, depth)
    denoise_a = CoolDegrain(clip, tr=1, thsad=72, thsadc=48, bits=depth, blksize=8, overlap=4)
    denoise_b = CoolDegrain(clip, tr=1, thsad=24, thsadc=48, bits=depth, blksize=8, overlap=4)
    return core.std.MaskedMerge(denoise_a, denoise_b, d_mask)


opstart = None
op_sf_a = f"[{opstart+378} {opstart+401}] [{opstart+1564} {opstart+1581}]" if opstart is not None else ""
op_sf_b = f"[{opstart+1728} {opstart+1757}]" if opstart is not None else ""


src = lvf.src(r"BDMV/[BDMV][ANZX-15507][Fate Grand Order - Absolute Demonic Front Babylonia][Vol.3][JP]/BDROM/DISC2/BDMV/STREAM/00007.m2ts")
src = src[24:-28]
src = fvf.Depth(src, 16)


h = 873
math_l = 0.5 * src.height / h * -1
scaled = _fractional_descale(src, h=h, b=1/5, c=2/5, src_left=.25)
credit_mask = _create_credit_mask(src, h=h, b=1/5, c=2/5)


denoise = fvf.rfs(_adap_denoise(scaled, luma_scaling=4, depth=16),
                  mvf.BM3D(scaled, sigma=[1,0.5], depth=16, profile1='lc'),
                  mappings=op_sf_a)

fix_lines = _fix_lineart(denoise)
merge_credits = core.std.MaskedMerge(fix_lines,
                                     fvf.Depth(src, get_depth(fix_lines)),
                                     fvf.Depth(credit_mask, get_depth(fix_lines)))

ref = core.f3kdb.Deband(merge_credits, range=6, y=72, cb=64, cr=64, grainy=0, grainc=0, output_depth=16)
deband = fvf.rfs(core.f3kdb.Deband(merge_credits, range=15, y=40, cb=32, cr=32, grainy=12, grainc=0, output_depth=16),
                 core.f3kdb.Deband(ref, range=14, y=48, cb=40, cr=40, grainy=24, grainc=0, output_depth=16),
                 mappings=op_sf_a)
deband = fvf.rfs(deband, core.f3kdb.Deband(merge_credits, range=12, y=56, cb=48, cr=48, grainy=36, grainc=0, output_depth=16),
                 mappings=op_sf_b)


grain = kgf.adaptive_grain(deband, 0.3, luma_scaling=4)


out = grain
final = fvf.Depth(out, 10)
final.set_output()
