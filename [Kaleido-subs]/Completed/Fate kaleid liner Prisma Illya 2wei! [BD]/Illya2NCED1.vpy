import vapoursynth as vs
import mvsfunc as mvf
import vsTAAmbk as taa	
import kagefunc as kgf
core = vs.core

src = core.lsmas.LWLibavSource(r"F:\Convert\[BDMV][Fate／kaleid liner プリズマ☆イリヤ ツヴァイ！ ][Vol.1-Vol.5+OVA Fin]\[BDMV][アニメ][141031]Fate／kaleid liner プリズマ☆イリヤ ツヴァイ！ Vol.2\BDROM\BDMV\STREAM\00012.m2ts")
src = core.std.Trim(src, 24, 2183)

scaled = kgf.inverse_scale(
    src, width=None, height=720, kernel='bicubic', a1=1/3, a2=1/3,
    kerneluv='blackman', mask_detail=False,denoise=False, use_gpu=True)
scaled = core.fmtc.bitdepth(scaled, bits=16)

srcY, srcU, srcV = kgf.split(scaled)
denoiseY = srcY.knlm.KNLMeansCL(3, 2, h=0.2)
denoiseY = mvf.BM3D(srcY, sigma=2, psample=1, radius1=1, ref=denoiseY)
denoised = kgf.join([denoiseY, srcU, srcV])

aa = taa.TAAmbk(denoised, aatype='Eedi3', opencl=True)

deband = core.f3kdb.Deband(aa, range=20, y=64, cb=56, cr=56, grainy=0, grainc=0, output_depth=16)

mask = kgf.retinex_edgemask(aa, sigma=1)
maskedmerge = core.std.MaskedMerge(deband, aa, mask)

out = kgf.adaptive_grain(maskedmerge, 0.3, mask_bits=10, luma_scaling=16, static=True)

final = core.fmtc.bitdepth(out, bits=10, dmode=3)
final.set_output()