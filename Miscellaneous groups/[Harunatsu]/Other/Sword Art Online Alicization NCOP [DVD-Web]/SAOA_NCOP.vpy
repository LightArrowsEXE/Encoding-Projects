import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import finesharp
import havsfunc as haf
import vsTAAmbk as taa
import adjust
core = vs.core

"""
	Note: this is not an official release. 
	This is something I started working that I could show Haru and be like "hey, you up for releasing this?".
	As of writing this I have not even brought it up to him yet, so don't get your hopes up as it's unlikely to happen until BDs hit (which I'm not encoding).
"""

src_a = lvf.src("Sword Art Online - Alicization E12 [1080p][AAC][JapDub][GerSub][Web-DL].mp4")
src_a = src_a[1581:3737]
src_a = core.resize.Spline36(src_a, 848, 480)
src_a = fvf.Depth(src_a, 16)

src_b = lvf.src("VTS_01_1.VOB.d2v")
src_b = src_b[6990:9690]
src_b = core.vivtc.VFM(src_b, 1)
src_b = core.vivtc.VDecimate(src_b)
src_b = src_b[0:2157]
src_b =  fvf.Depth(src_b, 16)
copy = src_b

src_b = core.std.CropRel(src_b, 2, 2, 0, 0)
src_b = core.resize.Spline36(src_b, 848, 480)
src_b = adjust.Tweak(src_b, sat=0.9, cont=1, bright=50)


# # # # DVD filtering # # # #
denoised = lvf.denoise(src_b, h=1.2)
sharpen = finesharp.sharpen(src_b, sstr=1.0)
darken = haf.FastLineDarkenMOD(sharpen, strength=24)

mask = kgf.retinex_edgemask(src_b, sigma=1).std.Binarize()
maskmerge = core.std.MaskedMerge(denoised, darken, mask)

#maskmerge = darken
aa = taa.TAAmbk(maskmerge, aatype='Eedi3')

dbn = core.f3kdb.Deband(aa, range=15, y=48, cb=40, cr=40, grainy=0, grainc=0, output_depth=16)

grain_1 = kgf.adaptive_grain(dbn, 1/2)
grain_2 = kgf.adaptive_grain(dbn, 1, static=False)
grain = fvf.rfs(grain_1, grain_2, mappings="[0 356] [415 424] [459 474] [551 616] [1025 1058] [1213 1227] [1263 1297] [1586 1695] [2018 2033]")

B = grain
# # # # DVD filtering # # # #


A = src_a
src = fvf.rfs(A, B, mappings="[373 474] [497 601] [617 723] [864 1024] [1074 1262] [1329 1432] [1458 2080]") # NOTE: mask Kirito at 565. Check scene with hardsubfademask at 1097, 1247, 1460.

kirito_mask = kgf.squaremask(src_a, 282, 480, 0, 0)
kiris_mask = core.imwri.Read(r"Kiris_mask.png").resize.Spline36(format=vs.GRAY16, matrix_s='709')
C_1a = core.std.MaskedMerge(B, A, kirito_mask)
C_1b = core.std.MaskedMerge(B, A, kiris_mask)
C_1 = fvf.rfs(C_1a, C_1b, mappings="[593 611]")

C = kgf.insert_clip(src, C_1[563:602], 563)

out = C
final = fvf.Depth(out, 10)
final.set_output()

