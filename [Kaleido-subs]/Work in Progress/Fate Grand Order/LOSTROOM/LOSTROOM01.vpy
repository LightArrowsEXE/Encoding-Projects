import vapoursynth as vs
import lvsfunc as lvf
import fvsfunc as fvf
import kagefunc as kgf
from nnedi3_rpow2 import nnedi3_rpow2
import vsTAAmbk as taa
core = vs.core

src = lvf.src(r"F:\Encode\[BDMV][Fate／Grand Order -MOONLIGHT／LOSTROOM-]\BDROM\BDMV\STREAM\00000.m2ts")
src = src[24:47090]
src = fvf.Depth(src, 16)

scaled = kgf.inverse_scale(src, height=720, kernel='bicubic', a1=0, a2=1, mask_detail=False, masking_areas=None)
scaled = nnedi3_rpow2(scaled)
scaled = core.resize.Spline36(scaled, 1920, 1080, format=vs.YUV420P16)

denoise = lvf.denoise(scaled, h=1.2)
aa = taa.TAAmbk(scaled, aatype='Eedi3', opencl=True)

deband = core.f3kdb.Deband(denoise, range=17, y=40, cb=32, cr=32, grainy=0, grainc=0, output_depth=16)

mask = kgf.retinex_edgemask(aa)
maskedmerge = core.std.MaskedMerge(deband, aa, mask)

comp = lvf.comp(src, maskedmerge, [10225, 25526, 31159, 38231, 41100, 42151])
comp.set_output()