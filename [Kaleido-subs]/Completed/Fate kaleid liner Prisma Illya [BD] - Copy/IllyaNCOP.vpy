import vapoursynth as vs
import mvsfunc as mvf
import vsTAAmbk as taa
import kagefunc as kgf
import havsfunc as haf
core = vs.get_core()
 
input = core.lsmas.LWLibavSource(r"F:\Convert\[BDMV] 魔法少女伊莉雅\[BDMV][131025][Fate Kaleid Liner Prisma Illya][Vol.02]\BDMV\STREAM\00010.m2ts")
input = core.std.Trim(input, 24, 2183)
#outro = core.lsmas.LWLibavSource(r"F:\Encoding\ffmpeg-20170918-18821e3-win64-static\bin\out (1) (1).mkv")
#outro = core.std.Trim(outro, 24, 39128)
input = core.fmtc.bitdepth(input, bits=16)

#scale
scaleY = kgf.inverse_scale(input, width=None, height=720, kernel='bicubic', a1=1/3, a2=1/3, kerneluv='blackman', mask_detail=False, masking_areas=None, mask_threshold=0.05, show_mask=False, denoise=False, use_gpu=False)
fix1 = core.std.Trim(scaleY, 1133, 1133)
fix2 = core.std.Trim(scaleY, 1135, 1135)
scaleY = core.remap.Rfs(scaleY, fix1, mappings="[1132 1132]")
scaleY = core.remap.Rfs(scaleY, fix2, mappings="[1134 1134]")

#dark mask
dinput = scaleY.dfttest.DFTTest(sigma=64, tbsize=1, sbsize=24, sosize=18)
dmask = core.std.Expr(kgf.getY(dinput), "x {} > x {} < and 255 0 ?".format(0, 55))
dmask = core.fmtc.bitdepth(dmask, bits=16)

scaled = core.fmtc.bitdepth(scaleY, bits=16)

#denoise
srcY = kgf.getY(scaled)	
denoiseY = srcY.knlm.KNLMeansCL(3, 2, h=0.2)
#denoiseY = haf.SMDegrain(srcY, tr=something, thsad=something, prefilter=3, RefineMotion=True)
#denoiseY = srcY.dfttest.DFTTest(sigma=64, tbsize=1, sbsize=24, sosize=20)
denoiseY = mvf.BM3D(denoiseY, sigma=2, psample=1, radius1=1, ref=denoiseY)

Uclip = core.std.ShufflePlanes(scaled, 1, colorfamily=vs.GRAY)
Vclip = core.std.ShufflePlanes(scaled, 2, colorfamily=vs.GRAY)

denoised = core.std.ShufflePlanes(clips=[denoiseY, Uclip, Vclip], planes=[0, 0, 0], colorfamily=vs.YUV)

#attempt at fixing lineart in final few cuts of OP
darken = haf.FastLineDarkenMOD(scaled, strength=48, protection=5, luma_cap=191, threshold=4, thinning=0)
remap = core.remap.Rfs(denoised, darken, mappings="[1895 2035]")

aa = taa.TAAmbk(remap, aatype='Eedi3', opencl=False, cycle=0)

#debanding & graining
deband = core.f3kdb.Deband(aa, range=20, y=64, cb=56, cr=56, grainy=24, grainc=0, output_depth=16)
deband2 = core.f3kdb.Deband(aa, range=21, y=56, cb=48, cr=48, grainy=36, grainc=0, output_depth=16)

grain = core.grain.Add(deband2, var=0.4, constant=True)
grain = core.std.MaskedMerge(deband, grain, dmask)

deband = kgf.adaptive_grain(deband, 0.3, mask_bits=10, luma_scaling=16, show_mask=False)

grain = core.remap.Rfs(deband, grain, mappings="[0 101] [1187 1894]")

#final merge
mask = kgf.retinex_edgemask(aa, sigma=1)
maskmerged = core.std.MaskedMerge(grain, aa, mask)

out = maskmerged
#out = core.std.Trim(out, 35023, 39104)

hist = core.fmtc.bitdepth(out, bits=10, dmode=3).set_output()
#hist = core.hist.Luma(hist).set_output()