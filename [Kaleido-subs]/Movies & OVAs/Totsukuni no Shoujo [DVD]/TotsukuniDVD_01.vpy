import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import havsfunc as haf
import mvsfunc as mvf
from vsutil import *
from vsTAAmbk import TAAmbk
core = vs.core


def detelecine(src):
    import functools
    def _postprocess(n, f, clip, deinterlaced):
        if f.props['_Combed'] > 0:
           return deinterlaced
        else:
           return clip    
    matched = core.vivtc.VFM(src, 1)
    src = core.nnedi3.nnedi3(src, field=1)
    return core.std.FrameEval(matched, functools.partial(_postprocess, clip=matched, deinterlaced=src), prop_src=matched)


def decimate(src):
    src = core.vivtc.VFM(src, 1)
    return core.vivtc.VDecimate(src)


src = lvf.src(r'G:\src\Totsukuni no Shoujo\VIDEO_TS\VTS_01_1.d2v')
src = detelecine(src).std.AssumeFPS(fpsnum=30000, fpsden=1001)
src = decimate(src)
src = fvf.Depth(src, 16)

scaled = core.resize.Bicubic(src, get_w(480), 480)

edge_mask = kgf.retinex_edgemask(scaled)
dehalo = haf.DeHalo_alpha(scaled, rx=3, darkstr=0)
dehalo = core.std.MaskedMerge(scaled, dehalo, edge_mask)

aa = TAAmbk(dehalo, aatype='Eedi3')
denoise = mvf.BM3D(aa, sigma=[2,0.5])
deband = core.f3kdb.Deband(denoise, range=13, y=24, cb=16, cr=16, grainy=0, grainc=0, output_depth=16)
grain = kgf.adaptive_grain(deband, 0.1, luma_scaling=16)


out = grain[:13217]+scaled[13217:]
final = fvf.Depth(out, 10)
final.set_output()
