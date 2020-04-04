import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import havsfunc as haf
from vsTAAmbk import TAAmbk
from vsutil import *
from cooldegrain import *
core = vs.core


def _create_dmask(clip: vs.VideoNode, luma_scaling: float, depth: Optional[int] = None) -> vs.VideoNode:
    if depth:
        clip = fvf.Depth(clip, depth)
    return core.adg.Mask(clip.std.PlaneStats(), luma_scaling)


def _adap_denoise(clip: vs.VideoNode, luma_scaling: float, depth: int) -> vs.VideoNode:
    denoise_a = CoolDegrain(clip, tr=1, thsad=72, thsadc=48, bits=depth, blksize=8, overlap=4)
    denoise_b = CoolDegrain(clip, tr=1, thsad=24, thsadc=48, bits=depth, blksize=8, overlap=4)
    return core.std.MaskedMerge(denoise_a, denoise_b, _create_dmask(clip, luma_scaling, depth))


def _create_credit_mask(clip: vs.VideoNode, h: int, 
                        kernel: str = 'bicubic', b: float = 1/3, c: float = 1/3,
                        brz: float = 0.05, out_h: int = None) -> vs.VideoNode:
    clip_y = get_y(clip)
    descaled = core.fmtc.resample(clip_y, get_w(h), h, kernel=kernel, a1=b, a2=c, invks=True)
    upscaled = core.fmtc.resample(descaled, clip_y.width, clip_y.height, kernel=kernel, a1=b, a2=c)
    credit_mask = core.std.Expr([clip_y, upscaled], 'x y - abs').std.Binarize(brz)
    credit_mask = kgf.iterate(credit_mask, core.std.Maximum, 6)
    credit_mask = kgf.iterate(credit_mask, core.std.Inflate, 2)
    if out_h:
        return core.resize.Spline36(credit_mask, get_w(h), h)
    return credit_mask


def _descaler(clip: vs.VideoNode, h: int, 
              kernel: str = 'bicubic', b: float = 1/3, c: float = 1/3,
              credit_mask: vs.VideoNode = None) -> vs.VideoNode:
    planes = split(clip)
    planes[0] = core.descale.Debicubic(planes[0], get_w(h), h, b, c)
    planes[1], planes[2] = [core.resize.Spline36(p, planes[0].width, planes[0].height, src_left=.25) for p in planes[1:]]

    merged = join(planes)
    if credit_mask is not None:
        clip = core.resize.Spline36(clip, get_w(h), h, merged.format)
        return core.std.MaskedMerge(merged, clip, credit_mask)
    return merged


def _adap_deband(clip: vs.VideoNode, luma_scaling: float, mappings: str = "") -> vs.VideoNode:
    deband_bright = core.f3kdb.Deband(clip, range=16, y=32, cb=24, cr=24, grainy=24, grainc=0, output_depth=16)
    deband_darker = core.f3kdb.Deband(clip, range=14, y=32, cb=24, cr=24, grainy=24, grainc=0, output_depth=16)
    merged = core.std.MaskedMerge(deband_bright, deband_darker, _create_dmask(clip, luma_scaling))
    return fvf.rfs(merged, deband_darker, mappings)


src = lvf.src(r'15/[Erai-raws] Honzuki no Gekokujou - Shisho ni Naru Tame ni wa Shudan wo Erandeiraremasen 2nd Season - 01 [1080p][Multiple Subtitle].mkv')
src = core.std.AssumeFPS(src, fpsnum=24000, fpsden=1001)
src = fvf.Depth(src, 32)


h = 812
b, c = 0, 1/2
scaled = _descaler(src, h, b=b, c=c)
scaled = core.resize.Spline36(scaled, get_w(810), 810)



denoise = _adap_denoise(scaled, luma_scaling=4, depth=16)
dehalo = haf.FineDehalo(denoise, rx=2.6, thmi=91, thma=191, darkstr=0, brightstr=1.1, contra=13)
aa = lvf.nneedi3_clamp(dehalo)


downscaled = core.resize.Spline36(src, get_w(810), 810, aa.format)
credit_mask = _create_credit_mask(src, h, b=b, c=c, brz=0.1, out_h=h)
credit_mask = core.resize.Spline36(credit_mask, get_w(810), 810, vs.GRAY16)
merged = core.std.MaskedMerge(aa, downscaled, credit_mask)

deband = _adap_deband(merged, luma_scaling=4)
grain = kgf.adaptive_grain(deband, 0.25, luma_scaling=4)


out = grain
final = fvf.Depth(out, 10)
final.set_output()
