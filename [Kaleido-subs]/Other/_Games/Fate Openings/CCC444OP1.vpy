import vapoursynth as vs
import mvsfunc as mvf
import vsTAAmbk as taa
import kagefunc as kgf
import fvsfunc as fvs
import havsfunc as haf
core = vs.get_core()

rineyemask_1 = core.imwri.Read(r"D:\Pictures\CCC masks\Rineye\mask_1.png").std.Binarize().resize.Spline36(matrix_s="709", format=vs.GRAY16)
rineyemask_2 = core.imwri.Read(r"D:\Pictures\CCC masks\Rineye\mask_2.png").std.Binarize().resize.Spline36(matrix_s="709", format=vs.GRAY16)
rineyemask_3 = core.imwri.Read(r"D:\Pictures\CCC masks\Rineye\mask_3.png").std.Binarize().resize.Spline36(matrix_s="709", format=vs.GRAY16)
rineyemask_4 = core.imwri.Read(r"D:\Pictures\CCC masks\Rineye\mask_4.png").std.Binarize().resize.Spline36(matrix_s="709", format=vs.GRAY16)
rineyemask_5 = core.imwri.Read(r"D:\Pictures\CCC masks\Rineye\mask_5.png").std.Binarize().resize.Spline36(matrix_s="709", format=vs.GRAY16)
rineyemask_6 = core.imwri.Read(r"D:\Pictures\CCC masks\Rineye\mask_6.png").std.Binarize().resize.Spline36(matrix_s="709", format=vs.GRAY16)
rineyemask_7 = core.imwri.Read(r"D:\Pictures\CCC masks\Rineye\mask_7.png").std.Binarize().resize.Spline36(matrix_s="709", format=vs.GRAY16)

rinmask_1 = core.imwri.Read(r"D:\Pictures\CCC masks\Rinface\mask_1.png").std.Binarize().resize.Spline36(matrix_s="709", format=vs.GRAY16)
rinmask_2 = core.imwri.Read(r"D:\Pictures\CCC masks\Rinface\mask_2.png").std.Binarize().resize.Spline36(matrix_s="709", format=vs.GRAY16)
rinmask_3 = core.imwri.Read(r"D:\Pictures\CCC masks\Rinface\mask_3.png").std.Binarize().resize.Spline36(matrix_s="709", format=vs.GRAY16)
rinmask_4 = core.imwri.Read(r"D:\Pictures\CCC masks\Rinface\mask_4.png").std.Binarize().resize.Spline36(matrix_s="709", format=vs.GRAY16)
rinmask_5 = core.imwri.Read(r"D:\Pictures\CCC masks\Rinface\mask_5.png").std.Binarize().resize.Spline36(matrix_s="709", format=vs.GRAY16)
rinmask_6 = core.imwri.Read(r"D:\Pictures\CCC masks\Rinface\mask_6.png").std.Binarize().resize.Spline36(matrix_s="709", format=vs.GRAY16)
rinmask_7 = core.imwri.Read(r"D:\Pictures\CCC masks\Rinface\mask_7.png").std.Binarize().resize.Spline36(matrix_s="709", format=vs.GRAY16)
rinmask_8 = core.imwri.Read(r"D:\Pictures\CCC masks\Rinface\mask_8.png").std.Binarize().resize.Spline36(matrix_s="709", format=vs.GRAY16)
rinmask_9 = core.imwri.Read(r"D:\Pictures\CCC masks\Rinface\mask_9.png").std.Binarize().resize.Spline36(matrix_s="709", format=vs.GRAY16)
rinmask_10 = core.imwri.Read(r"D:\Pictures\CCC masks\Rinface\mask_10.png").std.Binarize().resize.Spline36(matrix_s="709", format=vs.GRAY16)

mask_1 = core.imwri.Read(r"D:\Pictures\CCC masks\mask_1.png").std.Binarize().resize.Spline36(matrix_s="709", format=vs.GRAY16)
mask_2 = core.imwri.Read(r"D:\Pictures\CCC masks\mask_2.png").std.Binarize().resize.Spline36(matrix_s="709", format=vs.GRAY16)
mask_3 = core.imwri.Read(r"D:\Pictures\CCC masks\mask_3.png").std.Binarize().resize.Spline36(matrix_s="709", format=vs.GRAY16)
mask_4 = core.imwri.Read(r"D:\Pictures\CCC masks\mask_4.png").std.Binarize().resize.Spline36(matrix_s="709", format=vs.GRAY16)
mask_5 = core.imwri.Read(r"D:\Pictures\CCC masks\mask_5.png").std.Binarize().resize.Spline36(matrix_s="709", format=vs.GRAY16)
mask_6 = core.imwri.Read(r"D:\Pictures\CCC masks\mask_6.png").std.Binarize().resize.Spline36(matrix_s="709", format=vs.GRAY16)
mask_7 = core.imwri.Read(r"D:\Pictures\CCC masks\mask_7.png").std.Binarize().resize.Spline36(matrix_s="709", format=vs.GRAY16)
mask_8 = core.imwri.Read(r"D:\Pictures\CCC masks\mask_8.png").std.Binarize().resize.Spline36(matrix_s="709", format=vs.GRAY16)
mask_9 = core.imwri.Read(r"D:\Pictures\CCC masks\mask_9.png").std.Binarize().resize.Spline36(matrix_s="709", format=vs.GRAY16)
mask_10 = core.imwri.Read(r"D:\Pictures\CCC masks\mask_10.png").std.Binarize().resize.Spline36(matrix_s="709", format=vs.GRAY16)
mask_11 = core.imwri.Read(r"D:\Pictures\CCC masks\mask_11.png").std.Binarize().resize.Spline36(matrix_s="709", format=vs.GRAY16)
mask_12 = core.imwri.Read(r"D:\Pictures\CCC masks\mask_12.png").std.Binarize().resize.Spline36(matrix_s="709", format=vs.GRAY16)
mask_13 = core.imwri.Read(r"D:\Pictures\CCC masks\mask_13.png").std.Binarize().resize.Spline36(matrix_s="709", format=vs.GRAY16)
mask_14 = core.imwri.Read(r"D:\Pictures\CCC masks\mask_14.png").std.Binarize().resize.Spline36(matrix_s="709", format=vs.GRAY16)
mask_15 = core.imwri.Read(r"D:\Pictures\CCC masks\mask_15.png").std.Binarize().resize.Spline36(matrix_s="709", format=vs.GRAY16)

sakuramask_1 = core.imwri.Read(r"D:\Pictures\CCC masks\Sakurashoulder\mask_1.png").std.Binarize().resize.Spline36(matrix_s="709", format=vs.GRAY16)
sakuramask_2 = core.imwri.Read(r"D:\Pictures\CCC masks\Sakurashoulder\mask_2.png").std.Binarize().resize.Spline36(matrix_s="709", format=vs.GRAY16)
sakuramask_3 = core.imwri.Read(r"D:\Pictures\CCC masks\Sakurashoulder\mask_3.png").std.Binarize().resize.Spline36(matrix_s="709", format=vs.GRAY16)
sakuramask_4 = core.imwri.Read(r"D:\Pictures\CCC masks\Sakurashoulder\mask_4.png").std.Binarize().resize.Spline36(matrix_s="709", format=vs.GRAY16)

skirtmask_1 = core.imwri.Read(r"D:\Pictures\CCC masks\Skirtmask\mask_1.png").std.Binarize().resize.Spline36(matrix_s="709", format=vs.GRAY16)
skirtmask_2 = core.imwri.Read(r"D:\Pictures\CCC masks\Skirtmask\mask_2.png").std.Binarize().resize.Spline36(matrix_s="709", format=vs.GRAY16)
skirtmask_3 = core.imwri.Read(r"D:\Pictures\CCC masks\Skirtmask\mask_3.png").std.Binarize().resize.Spline36(matrix_s="709", format=vs.GRAY16)
skirtmask_4 = core.imwri.Read(r"D:\Pictures\CCC masks\Skirtmask\mask_4.png").std.Binarize().resize.Spline36(matrix_s="709", format=vs.GRAY16)
skirtmask_5 = core.imwri.Read(r"D:\Pictures\CCC masks\Skirtmask\mask_5.png").std.Binarize().resize.Spline36(matrix_s="709", format=vs.GRAY16)
skirtmask_6 = core.imwri.Read(r"D:\Pictures\CCC masks\Skirtmask\mask_6.png").std.Binarize().resize.Spline36(matrix_s="709", format=vs.GRAY16)
skirtmask_7 = core.imwri.Read(r"D:\Pictures\CCC masks\Skirtmask\mask_7.png").std.Binarize().resize.Spline36(matrix_s="709", format=vs.GRAY16)
skirtmask_8 = core.imwri.Read(r"D:\Pictures\CCC masks\Skirtmask\mask_8.png").std.Binarize().resize.Spline36(matrix_s="709", format=vs.GRAY16)
skirtmask_9 = core.imwri.Read(r"D:\Pictures\CCC masks\Skirtmask\mask_9.png").std.Binarize().resize.Spline36(matrix_s="709", format=vs.GRAY16)
skirtmask_10 = core.imwri.Read(r"D:\Pictures\CCC masks\Skirtmask\mask_10.png").std.Binarize().resize.Spline36(matrix_s="709", format=vs.GRAY16)
skirtmask_11 = core.imwri.Read(r"D:\Pictures\CCC masks\Skirtmask\mask_11.png").std.Binarize().resize.Spline36(matrix_s="709", format=vs.GRAY16)
skirtmask_12 = core.imwri.Read(r"D:\Pictures\CCC masks\Skirtmask\mask_12.png").std.Binarize().resize.Spline36(matrix_s="709", format=vs.GRAY16)
skirtmask_13 = core.imwri.Read(r"D:\Pictures\CCC masks\Skirtmask\mask_13.png").std.Binarize().resize.Spline36(matrix_s="709", format=vs.GRAY16)
skirtmask_14 = core.imwri.Read(r"D:\Pictures\CCC masks\Skirtmask\mask_14.png").std.Binarize().resize.Spline36(matrix_s="709", format=vs.GRAY16)
skirtmask_15 = core.imwri.Read(r"D:\Pictures\CCC masks\Skirtmask\mask_15.png").std.Binarize().resize.Spline36(matrix_s="709", format=vs.GRAY16)

bbmask_1 = core.imwri.Read(r"D:\Pictures\CCC masks\BBCollar\mask_1.png").std.Binarize().resize.Spline36(matrix_s="709", format=vs.GRAY16)
bbmask_2 = core.imwri.Read(r"D:\Pictures\CCC masks\BBCollar\mask_2.png").std.Binarize().resize.Spline36(matrix_s="709", format=vs.GRAY16)
bbmask_3 = core.imwri.Read(r"D:\Pictures\CCC masks\BBCollar\mask_3.png").std.Binarize().resize.Spline36(matrix_s="709", format=vs.GRAY16)
bbmask_4 = core.imwri.Read(r"D:\Pictures\CCC masks\BBCollar\mask_4.png").std.Binarize().resize.Spline36(matrix_s="709", format=vs.GRAY16)
bbmask_5 = core.imwri.Read(r"D:\Pictures\CCC masks\BBCollar\mask_5.png").std.Binarize().resize.Spline36(matrix_s="709", format=vs.GRAY16)
bbmask_6 = core.imwri.Read(r"D:\Pictures\CCC masks\BBCollar\mask_6.png").std.Binarize().resize.Spline36(matrix_s="709", format=vs.GRAY16)
bbmask_7 = core.imwri.Read(r"D:\Pictures\CCC masks\BBCollar\mask_7.png").std.Binarize().resize.Spline36(matrix_s="709", format=vs.GRAY16)
bbmask_8 = core.imwri.Read(r"D:\Pictures\CCC masks\BBCollar\mask_8.png").std.Binarize().resize.Spline36(matrix_s="709", format=vs.GRAY16)
bbmask_9 = core.imwri.Read(r"D:\Pictures\CCC masks\BBCollar\mask_9.png").std.Binarize().resize.Spline36(matrix_s="709", format=vs.GRAY16)

shift = 0
#manual shifting for lines: 126, 145, 153 and 166

denoisemap = f"[{shift+0} {shift+122}] [{shift+733} {shift+740}]"

debandmap1 = f"[{shift+733} {shift+782}] [{shift+961} {shift+1065}] [{shift+1342} {shift+1408}] [{shift+2072} {shift+2203}] [{shift+1762} {shift+1820}] [{shift+1274} {shift+1284}]"
debandmap2 = f"[{shift+1707} {shift+1761}]"
debandmap3 = f"[{shift+2032} {shift+2072}]"
debandmap4 = f"[{shift+259} {shift+275}] [{shift+381} {shift+410}] [{shift+733} {shift+740}] [{shift+1088} {shift+1208}] [{shift+1324} {shift+1341}] [{shift+1558} {shift+1605}] [{shift+1863} {shift+1884}]"

aamap = f"[{shift+411} {shift+512}] [{shift+1066} {shift+1087}] [{shift+1274} {shift+1284}]"
darkenmap = f"[{shift+1066} {shift+1087}] [{shift+1274} {shift+1284}]"

maskmergedmap = f"[{shift+733} {shift+782}] [{shift+1707} {shift+1790}]"
rineyemaskmap = f"[{shift+733} {shift+740}]"
rinmaskmap = f"[{shift+741} {shift+760}]"
legmaskmap = f"[{shift+1762} {shift+1790}]"
sakuramaskmap = f"[{shift+1748} {shift+1755}]"
bbmaskmap = f"[{shift+1791} {shift+1820}]"

grainmap1 = f"[{shift+191} {shift+258}] [{shift+513} {shift+528}] [{shift+733} {shift+782}] [{shift+961} {shift+1065}] [{shift+1345} {shift+1557}]"
grainmap2 = f"[{shift+1606} {shift+1862}]"

src = r"F:\Convert\FateEXTRA CCC\00001.mkv"
src = core.lsmas.LWLibavSource(src)
src = fvs.JIVTC(src, 0, draft=False, thr=15)
src = fvs.Depth(src, 16)

#scaled = core.resize.Bicubic(src, 1280, 720, filter_param_a=-0.6, filter_param_b=0.3)
scaled = fvs.Downscale444(src, 1280, 720, kernely='bicubic', invks=True, kerneluv='blackmanminlobe', a1y=-0.6, a2y=0.3)

srcY, srcU, srcV = kgf.split(scaled)
denoiseY1 = srcY.knlm.KNLMeansCL(3, 2, h=0.8)
denoiseY1 = mvf.BM3D(srcY, sigma=3, psample=1, radius1=1, ref=denoiseY1)
denoised1 = kgf.join([denoiseY1, srcU, srcV])
denoiseY2 = srcY.dfttest.DFTTest(sigma=12, tbsize=1, sbsize=24, sosize=18)
denoiseY2 = mvf.BM3D(srcY, sigma=5, psample=1, radius1=1, ref=denoiseY2)
denoised2 = kgf.join([denoiseY2, srcU, srcV])
denoised = core.remap.Rfs(denoised1, denoised2, mappings=denoisemap)

deband1 = core.f3kdb.Deband(denoised, range=18, y=64, cb=56, cr=56, grainy=0, grainc=0, output_depth=16)
deband2 = core.f3kdb.Deband(denoised, range=21, y=64, cb=56, cr=56, grainy=0, grainc=0, output_depth=16)
deband2 = core.f3kdb.Deband(deband2, range=5, y=300, cb=300, cr=300, grainy=12, grainc=0, output_depth=16)
deband3 = core.f3kdb.Deband(denoised, range=21, y=72, cb=64, cr=64, grainy=0, grainc=0, output_depth=16)
deband3 = core.f3kdb.Deband(deband3, range=5, y=200, cb=200, cr=200, grainy=36, grainc=0, output_depth=16)
deband4 = core.f3kdb.Deband(denoised, range=25, y=72, cb=64, cr=64, grainy=0, grainc=0, output_depth=16)
deband5 = core.f3kdb.Deband(denoised, range=12, y=40, cb=32, cr=32, grainy=0, grainc=0, output_depth=16)
deband = core.remap.Rfs(deband1, deband2, mappings=debandmap1)
deband = core.remap.Rfs(deband, deband3, mappings=debandmap2)
deband = core.remap.Rfs(deband, deband4, mappings=debandmap3)
deband = core.remap.Rfs(deband, deband5, mappings=debandmap4)

aa1 = taa.TAAmbk(scaled, aatype='Nnedi3', opencl=True)
aa2 = taa.TAAmbk(scaled, aatype='Eedi3', opencl=True)
aa = core.remap.Rfs(aa1, aa2, mappings=aamap)
dehalo = haf.FineDehalo(aa, darkstr=0)
darken = haf.FastLineDarkenMOD(dehalo, strength=36, protection=5, luma_cap=191, threshold=4, thinning=0)
darken = core.remap.Rfs(darken, scaled, mappings=darkenmap)

mask1 = kgf.retinex_edgemask(scaled, sigma=1).std.Inflate()
mask2 = kgf.retinex_edgemask(deband2, sigma=1)
mask2 = kgf.iterate(mask2, core.std.Maximum, 3)
mask2 = core.std.Binarize(mask2, 13000, planes=0).std.Inflate()
merged1 = core.std.MaskedMerge(deband, darken, mask1)
merged2 = core.std.MaskedMerge(deband, darken, mask2)
merged = core.remap.Rfs(merged1, merged2, mappings=maskmergedmap)

rem_1 = core.std.Merge(mask1, rineyemask_1).std.Binarize(13000, planes=0)
rem_2 = core.std.Merge(mask1, rineyemask_2).std.Binarize(13000, planes=0)
rem_3 = core.std.Merge(mask1, rineyemask_3).std.Binarize(13000, planes=0)
rem_4 = core.std.Merge(mask1, rineyemask_4).std.Binarize(13000, planes=0)
rem_5 = core.std.Merge(mask1, rineyemask_5).std.Binarize(13000, planes=0)
rem_6 = core.std.Merge(mask1, rineyemask_6).std.Binarize(13000, planes=0)
rem_7 = core.std.Merge(mask1, rineyemask_7).std.Binarize(13000, planes=0)
rineyemask = rem_1[0:734]+rem_2[734:735]+rem_3[735:736]+rem_4[736:737]+rem_5[737:738]+rem_6[738+739]+rem_7[739:741]
merged3 = core.std.MaskedMerge(merged, darken, rineyemask)
merged = core.remap.Rfs(merged, merged3, mappings=rineyemaskmap)

rm_1 = core.std.Merge(mask1, rinmask_1).std.Binarize(13000, planes=0)
rm_2 = core.std.Merge(mask1, rinmask_2).std.Binarize(13000, planes=0)
rm_3 = core.std.Merge(mask1, rinmask_3).std.Binarize(13000, planes=0)
rm_4 = core.std.Merge(mask1, rinmask_4).std.Binarize(13000, planes=0)
rm_5 = core.std.Merge(mask1, rinmask_5).std.Binarize(13000, planes=0)
rm_6 = core.std.Merge(mask1, rinmask_6).std.Binarize(13000, planes=0)
rm_7 = core.std.Merge(mask1, rinmask_7).std.Binarize(13000, planes=0)
rm_8 = core.std.Merge(mask1, rinmask_8).std.Binarize(13000, planes=0)
rm_9 = core.std.Merge(mask1, rinmask_9).std.Binarize(13000, planes=0)
rm_10 = core.std.Merge(mask1, rinmask_10).std.Binarize(13000, planes=0)
rinmask = rm_1[0:743]+rm_2[743:745]+rm_3[745:747]+rm_4[747:749]+rm_5[749:751]+rm_6[751:753]+rm_7[753:755]+rm_8[755:757]+rm_9[757:759]+rm_10[759:2205]
merged4 = core.std.MaskedMerge(merged, darken, rinmask)
merged = core.remap.Rfs(merged, merged4, mappings=rinmaskmap)

lm_1 = core.std.Merge(mask2, mask_1).std.Binarize(13000, planes=0)
lm_2 = core.std.Merge(mask2, mask_2).std.Binarize(13000, planes=0)
lm_3 = core.std.Merge(mask2, mask_3).std.Binarize(13000, planes=0)
lm_4 = core.std.Merge(mask2, mask_4).std.Binarize(13000, planes=0)
lm_5 = core.std.Merge(mask2, mask_5).std.Binarize(13000, planes=0)
lm_6 = core.std.Merge(mask2, mask_6).std.Binarize(13000, planes=0)
lm_7 = core.std.Merge(mask2, mask_7).std.Binarize(13000, planes=0)
lm_8 = core.std.Merge(mask2, mask_8).std.Binarize(13000, planes=0)
lm_9 = core.std.Merge(mask2, mask_9).std.Binarize(13000, planes=0)
lm_10 = core.std.Merge(mask2, mask_10).std.Binarize(13000, planes=0)
lm_11 = core.std.Merge(mask2, mask_11).std.Binarize(13000, planes=0)
lm_12 = core.std.Merge(mask2, mask_12).std.Binarize(13000, planes=0)
lm_13 = core.std.Merge(mask2, mask_13).std.Binarize(13000, planes=0)
lm_14 = core.std.Merge(mask2, mask_14).std.Binarize(13000, planes=0)
lm_15 = core.std.Merge(mask2, mask_15).std.Binarize(13000, planes=0)
legmask = lm_1[0:1764]+lm_2[1764:1766]+lm_3[1766:1768]+lm_4[1768:1770]+lm_5[1770:1772]+lm_6[1772:1774]+lm_7[1774:1776]+lm_8[1776:1778]+lm_9[1778:1780]+lm_10[1780:1782]+lm_11[1782:1784]+lm_12[1784:1786]+lm_13[1786:1788]+lm_14[1788:1790]+lm_15[1790:2205]
merged5 = core.std.MaskedMerge(merged, darken, legmask)
merged = core.remap.Rfs(merged, merged5, mappings=legmaskmap)

skm_1 = core.std.Merge(mask1, skirtmask_1).std.Binarize(13000, planes=0).std.Inflate().std.Binarize()
skm_2 = core.std.Merge(mask1, skirtmask_2).std.Binarize(13000, planes=0).std.Inflate().std.Binarize()
skm_3 = core.std.Merge(mask1, skirtmask_3).std.Binarize(13000, planes=0).std.Inflate().std.Binarize()
skm_4 = core.std.Merge(mask1, skirtmask_4).std.Binarize(13000, planes=0).std.Inflate().std.Binarize()
skm_5 = core.std.Merge(mask1, skirtmask_5).std.Binarize(13000, planes=0).std.Inflate().std.Binarize()
skm_6 = core.std.Merge(mask1, skirtmask_6).std.Binarize(13000, planes=0).std.Inflate().std.Binarize()
skm_7 = core.std.Merge(mask1, skirtmask_7).std.Binarize(13000, planes=0).std.Inflate().std.Binarize()
skm_8 = core.std.Merge(mask1, skirtmask_8).std.Binarize(13000, planes=0).std.Inflate().std.Binarize()
skm_9 = core.std.Merge(mask1, skirtmask_9).std.Binarize(13000, planes=0).std.Inflate().std.Binarize()
skm_10 = core.std.Merge(mask1, skirtmask_10).std.Binarize(13000, planes=0).std.Inflate().std.Binarize()
skm_11 = core.std.Merge(mask1, skirtmask_11).std.Binarize(13000, planes=0).std.Inflate().std.Binarize()
skm_12 = core.std.Merge(mask1, skirtmask_12).std.Binarize(13000, planes=0).std.Inflate().std.Binarize()
skm_13 = core.std.Merge(mask1, skirtmask_13).std.Binarize(13000, planes=0).std.Inflate().std.Binarize()
skm_14 = core.std.Merge(mask1, skirtmask_14).std.Binarize(13000, planes=0).std.Inflate().std.Binarize()
skm_15 = core.std.Merge(mask1, skirtmask_15).std.Binarize(13000, planes=0).std.Inflate().std.Binarize()
skirtmask = skm_1[0:1764]+skm_2[1764:1766]+skm_3[1766:1768]+skm_4[1768:1770]+skm_5[1770:1772]+skm_6[1772:1774]+skm_7[1774:1776]+skm_8[1776:1778]+skm_9[1778:1780]+skm_10[1780:1782]+skm_11[1782:1784]+skm_12[1784:1786]+skm_13[1786:1788]+skm_14[1788:1790]+skm_15[1790:2205]
skm_aa = taa.TAAmbk(deband5, aatype='Nnedi3', opencl=True)
skm_dehalo = haf.FineDehalo(skm_aa, darkstr=0)
skm_darken = haf.FastLineDarkenMOD(skm_dehalo, strength=36, protection=5, luma_cap=191, threshold=4, thinning=0)
skm_grain = core.grain.Add(src, var=1, uvar=0, constant=False)
merged5 = core.std.MaskedMerge(merged, skm_darken, skirtmask)
merged = core.remap.Rfs(merged, merged5, mappings=legmaskmap)

sm_1 = core.std.Merge(mask1, sakuramask_1).std.Binarize(13000, planes=0)
sm_2 = core.std.Merge(mask1, sakuramask_2).std.Binarize(13000, planes=0)
sm_3 = core.std.Merge(mask1, sakuramask_3).std.Binarize(13000, planes=0)
sm_4 = core.std.Merge(mask1, sakuramask_4).std.Binarize(13000, planes=0)
sakuramask = sm_1[0:1750]+sm_2[1750:1752]+sm_3[1752:1754]+sm_4[1754:1756]
merged6 = core.std.MaskedMerge(merged, darken, sakuramask)
merged = core.remap.Rfs(merged, merged6, mappings=sakuramaskmap)

bbm_1 = core.std.Merge(mask1, bbmask_1).std.Binarize(13000, planes=0)
bbm_2 = core.std.Merge(mask1, bbmask_2).std.Binarize(13000, planes=0)
bbm_3 = core.std.Merge(mask1, bbmask_3).std.Binarize(13000, planes=0)
bbm_4 = core.std.Merge(mask1, bbmask_4).std.Binarize(13000, planes=0)
bbm_5 = core.std.Merge(mask1, bbmask_5).std.Binarize(13000, planes=0)
bbm_6 = core.std.Merge(mask1, bbmask_6).std.Binarize(13000, planes=0)
bbm_7 = core.std.Merge(mask1, bbmask_7).std.Binarize(13000, planes=0)
bbm_8 = core.std.Merge(mask1, bbmask_8).std.Binarize(13000, planes=0)
bbm_9 = core.std.Merge(mask1, bbmask_9).std.Binarize(13000, planes=0)
bbmask = bbm_1[0:1797]+bbm_2[1797:1801]+bbm_3[1801:1803]+bbm_4[1803:1805]+bbm_5[1805:1811]+bbm_6[1811:1813]+bbm_7[1813:1815]+bbm_8[1815:1817]+bbm_9[1817:2205]
merged7 = core.std.MaskedMerge(merged, darken, bbmask)
merged = core.remap.Rfs(merged, merged7, mappings=bbmaskmap)

grain1 = kgf.adaptive_grain(merged, 1, mask_bits=10, luma_scaling=16, static=False, show_mask=False)
grain2 = kgf.adaptive_grain(merged, 0.5, mask_bits=10, luma_scaling=16, static=False, show_mask=False)
grain = core.remap.Rfs(merged, grain1, mappings=grainmap1)
grain = core.remap.Rfs(grain, grain2, mappings=grainmap2)

nograinmerge = core.std.MaskedMerge(grain, darken, rineyemask)
merged = core.remap.Rfs(grain, nograinmerge, mappings=rineyemaskmap)

final = fvs.Depth(merged, 10, dither_type='error_diffusion')
test = final[961:1342]
compare = core.resize.Spline36(src, 1280, 720)
final.set_output()