import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import vsTAAmbk as taa
core = vs.core
core.max_cache_size = 8192

opstart = 1318

src_a = lvf.src(r".\Kaguya-sama Love is War E01 [1080p][AAC][JapDub][GerSub][Web-DL].mp4")
src_a = src_a[0:35916]

src_b = lvf.src(r".\[HorribleSubs] Kaguya-sama wa Kokurasetai - 01 [1080p].mkv")
src_b = src_b[0:86]+src_b[88:16501]+src_b[16546:16556]+src_b[16557:]

mask = kgf.hardsubmask(src_a, src_b)
src = core.std.MaskedMerge(src_a, src_b, mask)
src = kgf.insert_clip(src, src_a[16502], 16502)
src = kgf.insert_clip(src, src_a[84], 84)
src = kgf.insert_clip(src, src[84], 85)

sqmask = kgf.squaremask(src, 723, 113, 598, 894)
src_sq = core.std.MaskedMerge(src_a, src_b, sqmask)
src = kgf.insert_clip(src, src_sq[27678:27699], 27678)

src_fade = fvf.Depth(kgf.hardsubmask_fades(src_a, src_b, highpass=1300), 8)
src_fade = core.std.MaskedMerge(src_a, src_b, src_fade)
src = fvf.ReplaceFramesSimple(src, src_fade, mappings=f"[{opstart+316} {opstart+443}] [10 27][39 55][1209 1317][3522 3584][6321 6426][9816 9821][16129 16132] [16074 16082][16556 16662][17209 17251][21004 21080][23177 23248][23387 23491][23658 23667][23716 23719][23806 23814][24394 24499][27012 27117][28534 28540][28564 28570][28594 28600][28624 28630][28657 28658][29795 29813][34250 34257][34304 34308][34446 34462][35761 35817]")

scaled = kgf.inverse_scale(src, width=None, height=874, kernel='bicubic', a1=0, a2=1/2, mask_detail=True, masking_areas=[[1209,opstart],[opstart,opstart+2159],[6322,6427],[24394,24499],[34578,35732]])
scaled = core.resize.Spline36(scaled, 1280, 720, format=vs.YUV444P16)

deblock = fvf.AutoDeblock(scaled)
deblock = fvf.rfs(scaled, deblock, mappings="[673 680] [682 698]")

denoise_a = lvf.denoise(scaled, h=0.4)
denoise_b = lvf.denoise(scaled, h=0.8)
denoise_c = lvf.denoise(scaled, h=1.2)
denoise = fvf.rfs(scaled, denoise_a, mappings="[298 335][670 765][916 981][3967 4094][8640 8693][9287 9532][9809 10156][10205 10306][10307 10510][10511 10636][10871 10957][11144 11185][11558 11858][11933 12322][12623 12644][12695 12874][12917 13219][13220 13299][13516 13761][13762 13791][13831 13965][14130 14363][15422 15529][15530 15787][15788 15875][15906 16230][16604 16849][17036 17251][17252 17372][17402 17820][18201 19058][19059 19166][19475 19768][19895 19966][20615 20680][20961 21152][21273 21900][22123 22176][22249 22536][22801 22935][22936 23248][23249 23539][24250 24367][24368 25089][25672 26091][26092 26433][26596 26679][26776 27192][27603 28058][28191 28310][28695 29432][29433 29516][29937 30233][30498 30557][30577 31415][31602 31733][32490 32843][32844 32975][33080 33113][33210 33251][33297 33542][34512 35915]")
denoise = fvf.rfs(denoise, denoise_b, mappings="[5100 5156][6873 6896][7709 7762][9143 9286][14538 14819][14987 15026][15185 15421][16504 16555][17390 17401][20531 20614][22051 22122][22177 22248][27193 27603][27699 27746][29517 29687][31869 31951][32143 32193][33114 33209][33717 34223][34224 34462]")
denoise = fvf.rfs(denoise, denoise_c, mappings="[15876 15905][22750 22800][27678 27698]")

aa_1 = taa.TAAmbk(denoise, aatype='Eedi3')
aa_2 = taa.TAAmbk(denoise, aatype='Eedi3', cycle=5) #THERE'S STILL ALIASING HOLY FUCKING SHIT
aa_mask = core.resize.Spline36(kgf.squaremask(scaled, 1280, 120, 0, 660), 1280, 720, format=vs.GRAY16)
aa_2 = core.std.MaskedMerge(aa_1, aa_2, aa_mask)
aa_3 = taa.TAAmbk(denoise, aatype='Eedi3', cycle=2)
aa = fvf.rfs(aa_1, aa_2, mappings="[23975 24073]")
aa = fvf.rfs(aa, aa_3, mappings="[24250 24321] [29937 30044]")

dbn_1 = core.f3kdb.Deband(aa, range=14, y=32, cb=24, cr=24, grainy=0, grainc=0, output_depth=16)
dbn_2 = core.f3kdb.Deband(aa, range=17, y=40, cb=32, cr=32, grainy=0, grainc=0, output_depth=16)
dbn_3 = core.f3kdb.Deband(aa, range=21, y=40, cb=32, cr=32, grainy=0, grainc=0, output_depth=16)
dbn_4 = core.f3kdb.Deband(aa, range=23, y=64, cb=56, cr=56, grainy=0, grainc=0, output_depth=16)
dbn_5 = core.f3kdb.Deband(aa, range=5, y=80, cb=72, cr=72, grainy=0, grainc=0, output_depth=16)
dbn_5 = core.f3kdb.Deband(dbn_5, range=18, y=64, cb=56, cr=56, grainy=24, grainc=0, output_depth=16)
dbn = fvf.rfs(aa, dbn_1, mappings="[58 141][506 552][593 664][766 801][916 1044][1078 1107][1138 1317][3943 3966][4209 4319][4911 5000][5100 5156][5613 5828][6450 6539][7763 7861][7862 8071][10205 10306][10871 10957][11144 11185][11558 11650][11669 11858][11933 12076][11933 12076][12695 12772][12917 13030][13079 13219][13741 13761][14987 15026][15185 15340][15422 15529][15530 15622][15641 15787][16515 16555][17036 17251][17516 17820][18321 18362][20961 21152][21333 21515][22249 22536][22936 22962][23099 23176][23249 23491][24250 24367][24692 24747][25672 26091][27193 27603][27603 28058][28695 29432][29433 29516][29937 30123][33080 33113][33717 33878][34224 34462]")
dbn = fvf.rfs(dbn, dbn_2, mappings="[298 335][673 698][1108 1137][3967 4033][5981 6190][6873 6896][7517 7708][8252 8329][9287 9412][10511 10636][15906 16230][16230 16493][17252 17372][17390 17401][18201 18320][18363 19058][19059 19166][19475 19768][19895 19966][20040 20098][20961 21080][21821 21900][22051 22122][22177 22248][22801 22935][23177 23248][26092 26433][26434 26499][26596 26679][27699 27746][28191 28310][29517 29687][30498 30557][30577 31415][31602 31733][31869 31951][32622 32843][32843 32975][33114 33251][34512 35915]")
dbn = fvf.rfs(dbn, dbn_3, mappings="[802 915][1053 1056][4034 4094][4095 4142][5379 5522][7360 7516][9143 9286][12077 12142][14538 14819][15185 15421][15623 15640][16504 16514][16742 16849][18099 18130][20531 20614][21516 21557][22750 22800][22963 23082][23492 23539][32143 32193][32490 32621]")
dbn = fvf.rfs(dbn, dbn_4, mappings="[7709 7762][10307 10510][13220 13299][27678 27698][33297 33542]")
dbn = fvf.rfs(dbn, dbn_5, mappings="[33879 34223]")

grain_1 = kgf.adaptive_grain(dbn, 0.3, luma_scaling=12)
grain_2 = kgf.adaptive_grain(dbn, 1, luma_scaling=12, static=False)
grain = fvf.rfs(dbn, grain_1, mappings="[298 335][766 915][1053 1056][3967 4142][4911 5000][5100 5156][5981 6190][6873 6896][7050 7359][8252 8329][10307 10510][11144 11185][12077 12142][13220 13299][13520 13556][14538 14819][15185 15421][15530 15787][15876 16230][16230 16493][16504 16555][16742 16849][17252 17372][17390 17401][18201 18320][18363 19058][19059 19166][19475 19768][19895 19966][20040 20098][20531 20614][20961 21080][21516 21557][22051 22122][22177 22536][22750 22935][22936 23082][23177 23248][23249 23539][23925 24073][26092 26163][26305 26433][26596 26679][27193 27603][27699 28058][28191 28310][28695 29432][29433 29516][29517 29687][30577 31415][31602 31733][31869 31951][32143 32193][32194 32400][32490 32621][32622 32843][32843 32975][32976 33079][33114 33209][33297 33542][33879 34223][34224 34462][34512 35746]")
grain = fvf.rfs(grain, grain_2, mappings="[7360 7516][7709 7762][9143 9286][27678 27698]")

# # # OP filtering # # #
op = src[opstart:opstart+2157]
op = core.resize.Spline36(op, 1280, 720, format=vs.YUV444P16)

op_denoise = lvf.denoise(op, h=0.4)

op_aa = taa.TAAmbk(op_denoise, aatype='Eedi3')

op_dbn_1 = core.f3kdb.Deband(op_aa, range=14, y=32, cb=24, cr=24, grainy=0, grainc=0, output_depth=16)
op_dbn_2 = core.f3kdb.Deband(op_aa, range=17, y=40, cb=32, cr=32, grainy=0, grainc=0, output_depth=16)
op_dbn_3 = core.f3kdb.Deband(op_aa, range=21, y=56, cb=48, cr=48, grainy=12, grainc=0, output_depth=16)
op_dbn = fvf.rfs(op_aa, op_dbn_1, mappings="[0 320][452 531][571 679][717 841][939 1109][1198 1459][1590 1685][1771 1856][1990 2035][2055 2084]")
op_dbn = fvf.rfs(op_dbn, op_dbn_2, mappings="[1110 1197][1686 1770][1857 1989]")
op_dbn = fvf.rfs(op_dbn, op_dbn_3, mappings="[1519 1589]")

op_grain = kgf.adaptive_grain(op_dbn, 0.3, luma_scaling=12)
# # # OP filtering # # #

op_out = op_grain
out = grain
final = kgf.insert_clip(out, op_out, opstart)
final = fvf.Depth(final, 10)
#final = final[7256:7256+814]
final.set_output() # TO-DO: nothing 