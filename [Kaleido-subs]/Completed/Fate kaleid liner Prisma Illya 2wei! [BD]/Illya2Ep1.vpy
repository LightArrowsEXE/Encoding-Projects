import vapoursynth as vs
import mvsfunc as mvf
import vsTAAmbk as taa	
import kagefunc as kgf
core = vs.core

edstart = 30547
debandframes = f'[5476 7708] [31515 33949]'
credits = f'[5476 7708] [31515 33948]'

src = core.lsmas.LWLibavSource(r"F:\Convert\[BDMV][Fate／kaleid liner プリズマ☆イリヤ ツヴァイ！ ][Vol.1-Vol.5+OVA Fin]\[BDMV][アニメ][140926]Fate／kaleid liner プリズマ☆イリヤ ツヴァイ！ Vol.1\FullDisc\BDROM\BDMV\STREAM\00008.m2ts")
src = core.std.Trim(src, 24, 33973)
src = core.fmtc.bitdepth(src, bits=16)

endcard = core.lsmas.LWLibavSource(r"F:\Convert\[BDMV][Fate／kaleid liner プリズマ☆イリヤ ツヴァイ！ ][Vol.1-Vol.5+OVA Fin]\[BDMV][アニメ][140926]Fate／kaleid liner プリズマ☆イリヤ ツヴァイ！ Vol.1\FullDisc\BDROM\BDMV\STREAM\00005.m2ts")
endcard = core.resize.Spline36(endcard, 1280, 720, format=vs.YUV444P16)
endcard = endcard + endcard[-1]*49

scaled = kgf.inverse_scale(
    src, width=None, height=720, kernel='bicubic', a1=1/3, a2=1/3,
    kerneluv='blackman', mask_detail=True, masking_areas=[[5476, 7708], [31515, 33948]],
    mask_threshold=0.05, show_mask=False, denoise=False, use_gpu=True)
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

aa = taa.TAAmbk(denoised, aatype='Eedi3', opencl=True)
aa2 = taa.TAAmbk(denoised, aatype='Nnedi3', opencl=True)
aa = core.remap.Rfs(aa, aa2, mappings="[6014 6144]")
aamaskmerged = core.std.MaskedMerge(aa, scaled, scaleYmiscmask)
aa = core.remap.Rfs(aa, aamaskmerged, mappings=credits)

#fix heavy aliasing
aa3 = taa.TAAmbk(aa, aatype=4, opencl=True, cycle=0)
aa = core.remap.Rfs(aa, aa3, mappings="[1449 1471]")

deband1 = core.f3kdb.Deband(aa, range=20, y=64, cb=56, cr=56, grainy=0, grainc=0, output_depth=16)
deband2 = core.f3kdb.Deband(aa, range=21, y=56, cb=48, cr=48, grainy=36, grainc=0, output_depth=16)
deband = core.remap.Rfs(deband1, deband2, mappings=debandframes)

mask = kgf.retinex_edgemask(aa, sigma=1)
maskedmerge = core.std.MaskedMerge(deband, aa, mask)

grain1 = kgf.adaptive_grain(maskedmerge, 0.3, mask_bits=10, luma_scaling=16, static=True)
grain2 = kgf.adaptive_grain(maskedmerge, 0.8, mask_bits=10, luma_scaling=16, static=False)
grain = core.remap.Rfs(grain1, grain2, mappings="[0 335]")
#grain = grain1

final = core.fmtc.bitdepth(grain, bits=10, dmode=3)
#final = core.std.Trim(final, 0, 239)
final.set_output()