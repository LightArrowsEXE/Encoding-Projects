import vapoursynth as vs
import fvsfunc as fvf
import kagefunc as kgf
import lvsfunc as lvf
import mvsfunc as mvf
import vsTAAmbk as taa
from nnedi3_rpow2 import nnedi3_rpow2
core = vs.core

opstart, edstart = 3427-2156, 32607-2156

src_a = lvf.src(r"16/Demon Slayer Kimetsu no Yaiba E16 [1080p][AAC][JapDub][GerSub][Web-DL].mkv")
src_b = lvf.src(r"16/[Erai-raws] Kimetsu no Yaiba - 16 [1080p][Multiple Subtitle].mkv")
src_b = src_b[1:]
scomp = lvf.scomp(src_a, src_b, height=480) # Matching

hardsubmask = kgf.hardsubmask(src_a, src_b)
src = core.std.MaskedMerge(src_a, src_b, hardsubmask)

src_fade = fvf.Depth(kgf.hardsubmask_fades(src_a, src_b, highpass=1300), 8)
src_fade = core.std.MaskedMerge(src_a, src_b, src_fade)
src = fvf.ReplaceFramesSimple(src, src_fade, mappings=f"[{opstart+2156} {opstart+3500}]")

op = src_a[opstart:opstart+2156] # dehardsub kills the OP (thanks CR)
src = kgf.insert_clip(src, op, opstart)
src = fvf.Depth(src, 16)


Y, U, V = kgf.split(src)
descaled = kgf.inverse_scale(Y, height=855, kernel='bicubic', b=0.2, c=0.4, mask_detail=True, denoise=True, bm3d_sigma=3, use_gpu=False)
descaled = fvf.Depth(descaled, 16)

aa_a = taa.TAAmbk(descaled, aatype='Nnedi3')
aa_b = taa.TAAmbk(descaled, aatype='Eedi3')
aa = fvf.rfs(aa_a, aa_b, mappings=f"[{opstart+292} {opstart+402}] [{opstart+1017} {opstart+1079}] [{opstart+1701} {opstart+1782}] [{opstart+1895} {opstart+1953}] [901 1014] [4627 4658] [4688 4717] [5043 5119] [5276 5488] [6532 6750] [6886 6993] [7192 7377] [7474 7841] [7911 8057] [8169 8273] [8382 8541] [8665 8814] [8929 9228] [9307 10235] [10396 10507] [10544 10667] [10719 10808] [10843 11130] [11623 11877] [11911 12018] [12508 12619] [12672 12743] [13014 13043] [13092 13121] [13145 13354] [13418 13483] [13664 14038] [14151 14720] [16198 16505] [16596 16781] [16812 16979] [17103 17426] [17523 17684] [18516 18562] [18617 18712] [19934 20026] [20083 20171] [20341 20544] [20598 20619] [20735 20766] [20843 21070] [21095 21318] [21719 21838] [21938 22015] [22106 22240] [22316 22393] [22575 22748] [22799 23032] [24753 25124] [25605 25778] [27533 27778]")

scaled = nnedi3_rpow2(aa).resize.Spline36(1920, 1080)
scaled = kgf.join([scaled, U, V])


denoise = mvf.BM3D(scaled, sigma=[3,2])
deband_a = core.f3kdb.Deband(denoise, range=18, y=40, cb=32, cr=32, grainy=12, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(denoise, range=21, y=48, cb=40, cr=40, grainy=12, grainc=0, output_depth=16)
deband = fvf.rfs(deband_a, deband_b, mappings=f"[{opstart+1128} {opstart+1287}] [22485 22574]")

grain_a = kgf.adaptive_grain(deband, 0.3)
grain_b = kgf.adaptive_grain(deband, 1)
grain = fvf.rfs(grain_a, grain_b, mappings=f"[{opstart+1128} {opstart+1287}] [8058 8168] [22485 22574]")


final = fvf.Depth(grain, 10)
final.set_output()