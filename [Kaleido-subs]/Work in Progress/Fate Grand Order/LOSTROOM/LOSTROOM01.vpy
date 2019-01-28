import vapoursynth as vs
import lvsfunc as lvf
import fvsfunc as fvf
import kagefunc as kgf
from nnedi3_rpow2 import nnedi3_rpow2
import vsTAAmbk as taa
core = vs.core
core.max_cache_size = 12288

src = lvf.src(r"F:\Encode\[BDMV][Fate／Grand Order -MOONLIGHT／LOSTROOM-]\BDROM\BDMV\STREAM\00000.m2ts")
src = src[24:47090]
src = fvf.Depth(src, 16)

scaled = kgf.inverse_scale(src, height=720, kernel='bicubic', a1=0, a2=1, mask_detail=True, masking_areas=[[0,3896]])
scaled = nnedi3_rpow2(scaled)
scaled = core.resize.Spline36(scaled, 1920, 1080, format=vs.YUV420P16)

denoise = lvf.denoise(scaled, h=2, sigma=6)
aa = taa.TAAmbk(scaled, aatype='Eedi3', opencl=True, cycle=1)

deband = core.f3kdb.Deband(denoise, range=21, y=56, cb=48, cr=48, grainy=12, grainc=0, output_depth=16)

mask = kgf.retinex_edgemask(aa)
maskedmerge = core.std.MaskedMerge(deband, aa, mask)

grain = kgf.adaptive_grain(maskedmerge, 1, luma_scaling=16, show_mask=False)

out = grain
final = fvf.Depth(out, 10)
final.set_output()