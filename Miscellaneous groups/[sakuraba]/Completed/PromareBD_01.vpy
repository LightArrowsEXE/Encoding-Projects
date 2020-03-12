import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import mvsfunc as mvf
import havsfunc as haf
from vsTAAmbk import TAAmbk
from vsutil import *
from cooldegrain import *
from nnedi3_rpow2 import *
core = vs.core


banded_scenes = """
                [7503 7634] [7767 7848] [8154 8343] [9577 9690] [13834 13872]
                [19328 19365] [19397 19601] [25065 25323] [25379 25426] [25579 25606] [25744 25818]
                [30701 30885]
                [31032 31400] [31581 31664] [32013 32029] [32063 32141] [32195 33517]
                [33731 33765]
                [40460 40838] [41070 41161] [41963 42132] [42386 42487] [43588 43662] [44333 44419]
                [46398 46912] [47882 48107] [52021 52091] [52498 52568] [55824 56039] [56960 57160]
                [57895 57946] [59503 59584] [59791 59964] [62222 62530] [62566 62660]
                [63605 63628] [64598 64679] [65133 65309] [65786 65842] [65999 66190] [66460 66615]
                [70739 70786] [70834 71333] [72005 72035] [72506 72583] [73012 73134]
                [73221 73543] [73770 73832] [73978 74338] [74469 74552]
                [74810 74876] [75776 75828] [75996 76055]
                [78774 78776] [78780 79100] [79196 79578] [79625 80321]
                [82582 82652] [83257 83415] [83544 83591] [83705 84057]
                [85163 85296] [85407 85487]
                [89283 89450] [90809 90850]
                [91861 92027] [92984 93042] [93179 93195] [94254 94528] [94538 94546]
                [95073 95444] [95725 96302] [96321 96386] [97469 97673]
                [99177 99236] [99379 99736] [99808 100309] [100444 100515]
                [100669 100685] [100720 100722] [101678 101879] [101900 102597] [102756 103898]
                [103920 104366] [104544 104757] [104966 105126] [105646 105752]
                [107424 107822] [108034 108176] [108273 108568] [108687 109028] [109327 109440]
                [109563 109664] [110673 110756] [111440 111547] [111661 111863] [112190 112652]
                [113661 113885] [113909 113942] [114195 114793] [114875 115125] [115215 115506] [115693 115925]
                [123321 123418] [124621 124962] [124985 125450] [125544 125826] [127030 127194] [128619 128857]
                [129373 129402] [129456 129809] [130616 130722] [130852 130917]
                [131815 132474] [132516 132732] [133891 134061] [134810 135107] [135215 135333]
                [137292 137392] [137742 137801] [138432 138484] [138779 138863] [141194 141268] [141336 142684]
                [142718 142932] [143053 143165] [143286 143499] [148541 148811]
                [150987 150998] [151580 151640] [152458 159216]
                """

ED_shots = """
           [150721 150909]
           [151016 151093]
           [151199 151276]
           [151313 151366]
           [151406 151460]
           [151486 151547]
           [151588 151640]
           [151671 151735]
           [151796 151828]
           [151869 151922]
           [151963 152014]
           [152054 152106]
           [152144 152197]
           [152235 152289]
           [152327 152380]
           [152482 152560]
           """

src_a = lvf.src(r"G:/src/PROMARE/BDMV/STREAM/00000.m2ts")
src_b = lvf.src(r"G:/src/PROMARE/BDMV/STREAM/00001.m2ts")
src_c = lvf.src(r"G:/src/PROMARE/BDMV/STREAM/00002.m2ts")

src = src_a+src_b+src_c
src = src[600:-24]
src = fvf.Depth(src, 32)

# Fix composition error
src = kgf.insert_clip(src, src[23670], 23671)


h = 892
b, c = .2620, .3690
planes = split(src)
descaled = core.descale.Debicubic(planes[0], get_w(h), h, b, c)
upscaled = core.resize.Bicubic(descaled, src.width, src.height, filter_param_a=b, filter_param_b=c)
credit_mask = core.std.Expr([planes[0], upscaled], 'x y - abs').std.Binarize(0.05)
credit_mask = kgf.iterate(credit_mask, core.std.Maximum, 6)
credit_mask = kgf.iterate(credit_mask, core.std.Inflate, 2)

upscaled_a = nnedi3_rpow2(descaled, width=src.width, height=src.height)
upscaled_b = lvf.upscaled_sraa(descaled, h=src.height, rfactor=2)
upscaled = fvf.rfs(upscaled_a, upscaled_b, mappings="[64124 64597]")

planes[0] = core.std.MaskedMerge(upscaled, planes[0], credit_mask)
scaled = join(planes)

# Replace possible full 1080p scenes that the mask might not catch
scaled = fvf.rfs(scaled, src, mappings="[5177 6940]")
scaled = fvf.Depth(scaled, 16)

interp = haf.QTGMC(scaled, InputType=1, TR2=3, Preset="Very Slow")
interp = fvf.rfs(scaled, interp, mappings="[24397 24516] [64124 64597] [98797 98903]" + ED_shots)

d_mask = kgf.adaptive_grain(interp, show_mask=True, luma_scaling=8)
denoise_a = CoolDegrain(interp, tr=1, thsad=72, thsadc=48, bits=16, blksize=8, overlap=4)
denoise_b = CoolDegrain(interp, tr=1, thsad=24, thsadc=48, bits=16, blksize=8, overlap=4)
denoise_c = mvf.BM3D(interp, sigma=[1.8,1], depth=16, profile1='lc')
denoise = core.std.MaskedMerge(denoise_a, denoise_b, d_mask)
denoise = fvf.rfs(denoise, denoise_c, mappings=banded_scenes)
diff = core.std.MakeDiff(interp, denoise_c)


aa_a = TAAmbk(denoise, aatype='Nnedi3')
aa_b = split(denoise)
aa_b[2] = TAAmbk(aa_b[2], aatype='Eedi3', cycle=1, repair=13)
aa_b = join(aa_b)
aa_c = lvf.upscaled_sraa(denoise, rfactor=2)
aa_d = TAAmbk(denoise, aatype='Eedi3', cycle=1, repair=13)
aa_e = lvf.nneedi3_clamp(denoise)
aa = fvf.rfs(aa_a, denoise, mappings=f"[152561 {src.num_frames-1}]")
aa = fvf.rfs(aa, aa_b, mappings="[59791 59885] [61771 61913] [66841 67538] [100669 100719]")
aa = fvf.rfs(aa, aa_c, mappings="[22412 22446] [80522 80568] [104544 104668]")
aa = fvf.rfs(aa, aa_d, mappings="[5347 5453] [21112 21206] [22447 22565] [24397 24516] [42897 42943] [71564 71787] [91225 91300] [101202 101250] [101900 103898] [108687 108916] [123321 123418] [124985 125205] [125827 125915] [134810 135024] [138242 138431] 138485 [151094 151113]" + ED_shots)
aa = fvf.rfs(aa, aa_e, mappings="[18244 18602] [62737 62874] [63629 63675]")


l_mask = kgf.retinex_edgemask(aa, 1)
deband_a = core.f3kdb.Deband(aa, range=14, y=48, cb=40, cr=40, grainy=32, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(aa, range=6, y=32, cb=32, cr=32, grainy=0, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(deband_b, range=21, y=32, cb=40, cr=40, grainy=24, grainc=0, output_depth=16)
deband_b = core.std.MaskedMerge(deband_b, aa, l_mask)
deband_b = core.rgvs.Repair(deband_b, deband_a, 13)
deband_b = core.std.MergeDiff(deband_b, diff)
deband = fvf.rfs(deband_a, deband_b, mappings=banded_scenes)

grain_a = kgf.adaptive_grain(deband, 1, luma_scaling=4)
grain_b = kgf.adaptive_grain(deband, 2.5, luma_scaling=4, static=False)
grain_c = kgf.adaptive_grain(deband, 1.5, luma_scaling=4, static=False)
grain_d = kgf.adaptive_grain(deband, 2, luma_scaling=4)
grain = fvf.rfs(grain_a, grain_b, mappings="[0 5453] [97338 97468]")
grain = fvf.rfs(grain, grain_c, mappings="[101874 104168]")
grain = fvf.rfs(grain, grain_d, mappings="[62353 62530] [62962 63135] [63511 63604] [65310 65369] [65406 65523] [65786 66190]")


out = grain
final = fvf.Depth(out, 10)
final.set_output()
