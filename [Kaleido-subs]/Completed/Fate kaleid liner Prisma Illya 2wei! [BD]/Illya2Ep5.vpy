import vapoursynth as vs
import mvsfunc as mvf
import vsTAAmbk as taa	
import kagefunc as kgf
core = vs.core

opstart = 984
edstart = 31457
debandframes = f'[{opstart+548} {opstart+702}] [{opstart+1008} {opstart+1368}] [{opstart+1462} {opstart+1512}] [{opstart+1592} {opstart+1650}] [{opstart+1780} {opstart+1887}] [{opstart+1949} {opstart+2159}] [593 600] [771 959] [29034 29087] [29142 29201] [29244 29726] [29775 30448]'
dynamicgrainframes = f'[{opstart} {opstart+55}] [{opstart+351} {opstart+483}] [{opstart+548} {opstart+702}] [{opstart+1008} {opstart+1368}] [{opstart+1462} {opstart+1512}] [{opstart+1592} {opstart+1650}] [{opstart+1780} {opstart+1887}] [{opstart+1949} {opstart+2159}]'
replaceframes = f'[{opstart+484} {opstart+512}] [{opstart+703} {opstart+1007}] [{opstart+1888} {opstart+1902}] [{opstart+1933} {opstart+1948}]'
credits = f'[{opstart} {opstart+2159}] [3129 3224] [{edstart} {edstart+2159}] [33591 33949]'

src = core.lsmas.LWLibavSource(r"F:\Convert\[BDMV][Fate／kaleid liner プリズマ☆イリヤ ツヴァイ！ ][Vol.1-Vol.5+OVA Fin]\[BDMV][アニメ][141128]Fate／kaleid liner プリズマ☆イリヤ ツヴァイ！ Vol.3\BDROM\BDMV\STREAM\00008.m2ts")
src = core.std.Trim(src, 24, 33974)
src = core.fmtc.bitdepth(src, bits=16)

endcard = core.lsmas.LWLibavSource(r"F:\Convert\[BDMV][Fate／kaleid liner プリズマ☆イリヤ ツヴァイ！ ][Vol.1-Vol.5+OVA Fin]\[BDMV][アニメ][141128]Fate／kaleid liner プリズマ☆イリヤ ツヴァイ！ Vol.3\BDROM\BDMV\STREAM\00005.m2ts")
endcard = core.resize.Spline36(endcard, 1280, 720, format=vs.YUV444P16)
endcard = endcard + endcard[-1]*49

scaled = kgf.inverse_scale(
    src, width=None, height=720, kernel='bicubic', a1=1/3, a2=1/3,
    kerneluv='blackman', mask_detail=True, masking_areas=[[opstart, opstart+2159],
    [3129, 3224], [edstart, edstart+2159], [33591, 33949]], mask_threshold=0.05, 
    show_mask=False, denoise=False, use_gpu=True)
scaled = core.fmtc.bitdepth(scaled, bits=16)
scaled = scaled + endcard

srcY, srcU, srcV = kgf.split(scaled)
denoiseY = srcY.knlm.KNLMeansCL(3, 2, h=0.2)
denoiseY = mvf.BM3D(denoiseY, sigma=2, psample=1, radius1=1)
denoised = kgf.join([denoiseY, srcU, srcV])

scaleYmiscmask = kgf.inverse_scale(
    src, width=None, height=720, kernel='bicubic', a1=1/3, a2=1/3,
    kerneluv='blackman', mask_detail=True, masking_areas=None, 
    mask_threshold=0.05, show_mask=True, denoise=False, use_gpu=True)
scaleYmiscmask = core.fmtc.bitdepth(scaleYmiscmask, bits=16)

aa1 = taa.TAAmbk(denoised, aatype='Eedi3', opencl=True)
aa2 = taa.TAAmbk(denoised, aatype='Nnedi3', opencl=True)
aa = core.remap.Rfs(aa1, aa2, mappings="[20427 20510]")
aamaskmerged = core.std.MaskedMerge(aa, scaled, scaleYmiscmask)
aa = core.remap.Rfs(aa, aamaskmerged, mappings=credits)

deband1 = core.f3kdb.Deband(aa, range=20, y=64, cb=56, cr=56, grainy=0, grainc=0, output_depth=16)
deband2 = core.f3kdb.Deband(aa, range=21, y=56, cb=48, cr=48, grainy=36, grainc=0, output_depth=16)
deband = core.remap.Rfs(deband1, deband2, mappings=debandframes)

mask = kgf.retinex_edgemask(aa, sigma=1)
maskedmerge = core.std.MaskedMerge(deband, aa, mask)

grain1 = kgf.adaptive_grain(maskedmerge, 0.3, mask_bits=10, luma_scaling=16, static=True)
grain2 = kgf.adaptive_grain(maskedmerge, 0.5, mask_bits=10, luma_scaling=16, static=False)
grain = core.remap.Rfs(grain1, grain2, mappings=dynamicgrainframes)

out = core.remap.Rfs(grain, aa, mappings=replaceframes)

final = core.fmtc.bitdepth(out, bits=10, dmode=3)
final.set_output()