import vapoursynth as vs
import mvsfunc as mvf
import vsTAAmbk as taa	
import kagefunc as kgf
import havsfunc as haf
from nnedi3_rpow2 import nnedi3_rpow2
core = vs.core
 
input = core.lsmas.LWLibavSource(r"F:\Convert\[BDMV] 魔法少女伊莉雅\[BDMV][130927][[Fate Kaleid Liner Prisma Illya][Vol.01]\BDMV\STREAM\00007.m2ts")
input = core.std.Trim(input, 24, 39128)
input = core.fmtc.bitdepth(input, bits=16)

#endcard scaling
endcard = core.lsmas.LWLibavSource("F:\Convert\[BDMV] 魔法少女伊莉雅\[BDMV][130927][[Fate Kaleid Liner Prisma Illya][Vol.01]\BDMV\STREAM/00004.m2ts")
endcard = core.resize.Spline36(endcard, 1280, 720, format=vs.YUV444P16)
endcard = endcard + endcard[-1]*49

#scale
scaled = kgf.inverse_scale(input, width=None, height=720, kernel='bicubic', a1=1/3, a2=1/3, kerneluv='blackman', mask_detail=True, masking_areas= [[7529, 9775], [36683, 39103]], mask_threshold=0.05, show_mask=False, denoise=False, use_gpu=False)

scaled = kgf.insert_clip(scaled, scaled[8662], 8661)
scaled = kgf.insert_clip(scaled, scaled[8664], 8663)

scaled = core.fmtc.bitdepth(scaled, bits=16)
scaled = scaled + endcard

#denoise
srcY, srcU, srcV = kgf.split(scaled)
denoiseY = srcY.knlm.KNLMeansCL(3, 2, h=0.2)
#denoiseY = haf.SMDegrain(srcY, tr=something, thsad=something, prefilter=3, RefineMotion=True)
#denoiseY = srcY.dfttest.DFTTest(sigma=64, tbsize=1, sbsize=24, sosize=20)
denoiseY = mvf.BM3D(denoiseY, sigma=2, psample=1, radius1=1)

denoised = kgf.join([denoiseY, srcU, srcV])

#attempt at fixing lineart in final few cuts of OP
darken = haf.FastLineDarkenMOD(scaled, strength=48, protection=5, luma_cap=191, threshold=4, thinning=0)
remap = core.remap.Rfs(denoised, darken, mappings="[9424 9564]")

aa = taa.TAAmbk(remap, aatype='Eedi3', opencl=True, cycle=0)

#replacing aa'd credits with non-aa'd credits because AA blurs them
scaleYmiscmask = kgf.inverse_scale(input, width=None, height=720, kernel='bicubic', a1=1/3, a2=1/3, kerneluv='blackman', mask_detail=True, masking_areas=None, mask_threshold=0.05, show_mask=True, denoise=False, use_gpu=False)
scaleYmiscmask = core.fmtc.bitdepth(scaleYmiscmask, bits=16)
aamaskmerged = core.std.MaskedMerge(aa, scaled, scaleYmiscmask)
aa = core.remap.Rfs(aa, aamaskmerged, mappings="[7529 9775] [36683 39104]")

#debanding & graining
deband1 = core.f3kdb.Deband(aa, range=20, y=64, cb=56, cr=56, grainy=0, grainc=0, output_depth=16)
deband2 = core.f3kdb.Deband(aa, range=21, y=56, cb=48, cr=48, grainy=36, grainc=0, output_depth=16)
deband3 = core.f3kdb.Deband(aa, range=23, y=72, cb=64, cr=64, grainy=36, grainc=0, output_depth=16)

grain1 = kgf.adaptive_grain(deband1, 0.3, mask_bits=10, luma_scaling=16, show_mask=False)
grain2 = kgf.adaptive_grain(deband2, 0.3, mask_bits=10, luma_scaling=16, show_mask=False)
grain3 = kgf.adaptive_grain(deband3, 0.8, mask_bits=10, luma_scaling=16, show_mask=False)

grain = core.remap.Rfs(grain1, grain2, mappings="[7529 7630] [8194 8329] [8716 9423] [10140 10206] [11233 11387] [13495 13643] [13676 18200] [20235 20299] [20529 20986] [21010 21098] [26897 36682] [38841 39104] [39104 39177]")
grain = core.remap.Rfs(grain, grain3, mappings="[13644 13675]")

#final merge
mask = kgf.retinex_edgemask(aa, sigma=1)
maskmerged = core.std.MaskedMerge(grain, aa, mask)

final = core.fmtc.bitdepth(maskmerged, bits=10, dmode=3)
final.set_output()
#hist = core.hist.Luma(hist).set_output()