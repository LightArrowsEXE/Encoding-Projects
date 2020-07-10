import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import havsfunc as haf
import descale as ds
from vsutil import *
from cooldegrain import *
core = vs.core


def _create_credit_mask(clip: vs.VideoNode, h: int,
                        kernel: str = 'bicubic', b: float = 1/3, c: float = 1/3,
                        brz: float = 0.05, out_h: int = None) -> vs.VideoNode:
    clip_y = get_y(clip)
    descaled = core.descale.Debicubic(clip_y, get_w(h), h, b, c)
    upscaled = core.resize.Bicubic(descaled, clip_y.width, clip_y.height, filter_param_a=b, filter_param_b=c)
    credit_mask = core.std.Expr([clip_y, upscaled], 'x y - abs').std.Binarize(brz)
    credit_mask = kgf.iterate(credit_mask, core.std.Maximum, 6)
    credit_mask = kgf.iterate(credit_mask, core.std.Inflate, 2)
    if out_h:
        return core.resize.Spline36(credit_mask, get_w(h), h)
    return credit_mask


src = lvf.src(r'21/[HorribleSubs] Honzuki no Gekokujou - 21 [1080p].mkv')
src = core.std.AssumeFPS(src, fpsnum=24000, fpsden=1001)
src = fvf.Depth(src, 32)


h = 812
b, c = 0, 1/2
scaled = ds.Debicubic(src, get_w(h), h, yuv444=True)
scaled = core.resize.Bicubic(scaled, get_w(810), 810)


denoise = CoolDegrain(scaled, tr=1, thsad=72, thsadc=48, bits=16, blksize=8, overlap=4)

planes = split(denoise)
planes[0] = lvf.aa.nneedi3_clamp(planes[0])
aa = join(planes) # One day I'll make clamp do this internally

downscaled = core.resize.Spline36(src, get_w(810), 810, aa.format)
credit_mask = _create_credit_mask(src, h, b=b, c=c, brz=0.1).resize.Spline36(get_w(810), 810, vs.GRAY16)
merged = core.std.MaskedMerge(aa, downscaled, credit_mask)

deband = core.f3kdb.Deband(merged, range=15, y=32, cb=24, cr=24, grainy=0, grainc=0, output_depth=16)
grain = kgf.adaptive_grain(deband, 0.25, luma_scaling=4)


out = grain
final = fvf.Depth(out, 10)
final.set_output()
