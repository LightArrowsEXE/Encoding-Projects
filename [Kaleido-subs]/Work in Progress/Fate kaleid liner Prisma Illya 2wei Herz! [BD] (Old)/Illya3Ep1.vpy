import vapoursynth as vs
import mvsfunc as mvf
import vsTAAmbk as taa	
import kagefunc as kgf
core = vs.core

opstart = 0
edstart = 0
denoiseframesOP = f'[{opstart+0} {opstart+499}] [{opstart+859} {opstart+918}] [{opstart+1804} {opstart+1868}] [{opstart+1974} {opstart+2029}]'
debandframesOPa = f'[{opstart+0} {opstart+142}] [{opstart+824} {opstart+858}] [{opstart+919} {opstart+960}] [{opstart+2029} {opstart+2159}]'
debandframesOPb = f'[{opstart+1334} {opstart+1801}]'
dynamicgrainframesOP = f'[{opstart+824} {opstart+858}] [{opstart+1334} {opstart+1739}]'
replaceframesOP = f'[{opstart+0} {opstart+499}] [{opstart+859} {opstart+918}] [{opstart+1146} {opstart+1333}] [{opstart+1804} {opstart+1868}] [{opstart+1974} {opstart+2029}]'
creditsOPED = f'[{opstart+0} {opstart+2159}] [{edstart+0} {edstart+2159}]'

denoiseframes = f'[1 1]'
credits = f'[2 2]'
debandframes = f'[3 3]'
dynamicgrainframes = f'[4 4]'
replaceframes = f'[5 5]'

src = core.lsmas.LWLibavSource(r"F:\Convert\Fate／kaleid liner プリズマ☆イリヤ ツヴァイ ヘルツ!Vol.1~Vol.5\[BDMV][アニメ][150925]Fate／kaleid liner プリズマ☆イリヤ ツヴァイ ヘルツ! Vol.1\BDMV\STREAM\00008.m2ts")
src = core.std.Trim(src, 24, 30281)

endcard = core.lsmas.LWLibavSource(r"F:\Convert\[BDMV][Fate／kaleid liner プリズマ☆イリヤ ツヴァイ！ ][Vol.1-Vol.5+OVA Fin]\[BDMV][アニメ][150130]Fate／kaleid liner プリズマ☆イリヤ ツヴァイ！ Vol.5\BDROM\BDMV\STREAM\00005.m2ts")
endcard = core.resize.Spline36(endcard, 1280, 720, format=vs.YUV444P16)
endcard = endcard + endcard[-1]*49

scaled = kgf.inverse_scale(
    src, width=None, height=720, kernel='bicubic', a1=1/3, a2=1/3,
    kerneluv='blackman', mask_detail=True, masking_areas=[[opstart, opstart+2159],
    [3457, 3511], [25160, 27297]], mask_threshold=0.05, show_mask=False, 
    denoise=False, use_gpu=True)
scaled = core.fmtc.bitdepth(scaled, bits=16)
scaled = scaled + endcard

srcY, srcU, srcV = kgf.split(scaled)
denoiseY1 = srcY.knlm.KNLMeansCL(3, 2, h=0.2)
denoiseY1 = mvf.BM3D(denoiseY1, sigma=2, psample=1, radius1=1)
denoiseY2 = srcY.knlm.KNLMeansCL(3, 2, h=1.2)
denoiseY2 = mvf.BM3D(denoiseY2, sigma=3, psample=1, radius1=1)
denoiseY = core.remap.Rfs(denoiseY1, denoiseY2, mappings=denoiseframesOP)
denoiseY = core.remap.Rfs(denoiseY, denoiseY2, mappings=denoiseframes)
denoised = kgf.join([denoiseY, srcU, srcV])

scaleYmiscmask = kgf.inverse_scale(
    src, width=None, height=720, kernel='bicubic', a1=1/3, a2=1/3,
    kerneluv='blackman', mask_detail=True, masking_areas=None, 
    mask_threshold=0.05, show_mask=True, denoise=False, use_gpu=True)
scaleYmiscmask = core.fmtc.bitdepth(scaleYmiscmask, bits=16)

aa = taa.TAAmbk(denoised, aatype='Eedi3', opencl=True)
aamaskmerged = core.std.MaskedMerge(aa, scaled, scaleYmiscmask)
aa = core.remap.Rfs(aa, aamaskmerged, mappings=creditsOPED)
aa = core.remap.Rfs(aa, aamaskmerged, mappings=credits)

deband1 = core.f3kdb.Deband(aa, range=20, y=64, cb=56, cr=56, grainy=0, grainc=0, output_depth=16)
deband2 = core.f3kdb.Deband(aa, range=21, y=56, cb=48, cr=48, grainy=36, grainc=0, output_depth=16)
deband3 = core.f3kdb.Deband(aa, range=14, y=48, cb=40, cr=40, grainy=12, grainc=0, output_depth=16)
deband = core.remap.Rfs(deband1, deband2, mappings=debandframesOPa)
deband = core.remap.Rfs(deband, deband3, mappings=debandframesOPb)
deband = core.remap.Rfs(deband, deband2, mappings=debandframes)

mask = kgf.retinex_edgemask(aa, sigma=1)
maskedmerge = core.std.MaskedMerge(deband, aa, mask)

grain1 = kgf.adaptive_grain(maskedmerge, 0.3, mask_bits=10, luma_scaling=16, static=True)
grain2 = kgf.adaptive_grain(maskedmerge, 0.8, mask_bits=10, luma_scaling=16, static=False)
grain = core.remap.Rfs(grain1, grain2, mappings=dynamicgrainframesOP)
grain = core.remap.Rfs(grain, grain2, mappings=dynamicgrainframes)

out = core.remap.Rfs(grain, aa, mappings=replaceframesOP)
out = core.remap.Rfs(out, aa, mappings=replaceframes)

final = core.fmtc.bitdepth(out, bits=10, dmode=3)
final.set_output()