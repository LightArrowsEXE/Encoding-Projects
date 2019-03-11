import vapoursynth as vs
import lvsfunc as lvf
import fvsfunc as fvf
import kagefunc as kgf
import havsfunc as haf
import vsTAAmbk as taa
from nnedi3_rpow2 import nnedi3_rpow2
core = vs.core
core.max_cache_size = 8096

src = lvf.src(r"../[BDMV][Fate／Grand Order -MOONLIGHT／LOSTROOM-]/BDROM/BDMV/STREAM/00006.m2ts")
src = src[24:384]
src = fvf.Depth(src, 16)
Y, U, V = kgf.split(src)

scaled = kgf.inverse_scale(src, height=720, kernel='bilinear')
scaled = nnedi3_rpow2(scaled).resize.Spline36(1920, 1080, format=vs.YUV420P16)
scaled_m = kgf.inverse_scale(src, height=873, mask_detail=True, show_mask=True).resize.Spline36(1920, 1080, format=vs.GRAY16)
scaled = core.std.MaskedMerge(scaled, src, scaled_m)
scaled = kgf.join([scaled, U, V])

denoise = lvf.qden(scaled, h=1)
deband = core.f3kdb.Deband(denoise, range=17, y=32, cb=24, cr=24, grainy=0, grainc=0, output_depth=16)
sharpen = haf.ContraSharpening(deband, src, radius=None, rep=13)

aa = taa.TAAmbk(scaled, aatype='Eedi3', opencl=True)

mask = kgf.retinex_edgemask(aa, 1)
maskedmerge = core.std.MaskedMerge(sharpen, aa, mask)

out = maskedmerge
final = fvf.Depth(out, 10)
comp = lvf.comp(src, out, [35, 62, 107, 117, 137, 151, 162, 214, 248, 258, 279])
comp.set_output()