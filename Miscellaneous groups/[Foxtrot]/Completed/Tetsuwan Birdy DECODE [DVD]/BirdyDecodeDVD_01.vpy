import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import havsfunc as haf
from vsutil import *
from nnedi3_rpow2 import *
from cooldegrain import *
core = vs.core
core.num_threads = 2


src = lvf.src(r'DVDISO/(DVDISO)(アニメ) 鉄腕バーディー DECODE VOLUME01 (080924)(iso+mds+jpg)/TETSUWAN_BIRDY_01.d2v')
src = src[4485:47043]
src = lvf.decomb(src, TFF=True)
crop = core.std.CropRel(src, 2, 2)
ef = core.edgefixer.ContinuityFixer(crop, [2,1,1], 0, [2,1,1], 0)
ef = fvf.Depth(ef, 32)

planes = split(ef)
planes[0] = nnedi3_rpow2(planes[0]).resize.Spline36(get_w(486, 16/9), 486)
planes[1], planes[2] = [core.resize.Bicubic(p, planes[0].width/2, planes[0].height/2) for p in planes[1:]]
scaled = fvf.Depth(join(planes), 16)


darken = haf.FastLineDarkenMOD(scaled, strength=24)

d_mask = kgf.adaptive_grain(darken, show_mask=True, luma_scaling=8)
denoise_a = CoolDegrain(darken, tr=1, thsad=72, thsadc=48, bits=16, blksize=8, overlap=4)
denoise_b = CoolDegrain(darken, tr=1, thsad=24, thsadc=48, bits=16, blksize=8, overlap=4)
denoise = core.std.MaskedMerge(denoise_a, denoise_b, d_mask)

deband = core.f3kdb.Deband(denoise, range=13, y=24, cb=16, cr=16, grainy=12, grainc=0, output_depth=16)
grain = kgf.adaptive_grain(deband, 0.1, luma_scaling=8)


out = grain
final = fvf.Depth(out, 10)
final.set_output()
