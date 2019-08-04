import vapoursynth as vs
import fvsfunc as fvf
import kagefunc as kgf
import lvsfunc as lvf
import mvsfunc as mvf
import vsTAAmbk as taa
from nnedi3_rpow2 import nnedi3_rpow2
core = vs.core

opstart, edstart = 4267-2156, 33086-2156

src_a = lvf.src(r"18/Demon Slayer Kimetsu no Yaiba E18 [1080p][AAC][JapDub][GerSub][Web-DL].mkv")
src_b = lvf.src(r"18/[Erai-raws] Kimetsu no Yaiba - 18 [1080p][Multiple Subtitle].mkv")
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
descaled = kgf.inverse_scale(Y, height=855, kernel='bicubic', b=0.2, c=0.4, mask_detail=True,)
descaled = fvf.Depth(descaled, 16)

aa_a = taa.TAAmbk(descaled, aatype='Nnedi3')
aa_b = taa.TAAmbk(descaled, aatype='Eedi3')
aa_c = lvf.NnEedi3(descaled)
aa = fvf.rfs(aa_a, aa_b, mappings=f"[{opstart+292} {opstart+402}] [{opstart+1017} {opstart+1079}] [{opstart+1701} {opstart+1782}] [{opstart+1895} {opstart+1953}] [9689 9808] [12645 12858] [13029 13362] [14439 14520] [15363 15421] [15815 15982] [20496 20522] [20553 20572] [20598 20657] [21099 21265] [29864 30011] [30242 30412] [30647 30657] [30752 30833]")
aa = fvf.rfs(aa, aa_c, mappings="")

scaled = nnedi3_rpow2(aa).resize.Spline36(1920, 1080)
scaled = kgf.join([scaled, U, V])


denoise = mvf.BM3D(scaled, sigma=[3,2])
deband_a = core.f3kdb.Deband(denoise, range=18, y=40, cb=32, cr=32, grainy=12, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(denoise, range=21, y=48, cb=40, cr=40, grainy=12, grainc=0, output_depth=16)
deband = fvf.rfs(deband_a, deband_b, mappings=f"[{opstart+1128} {opstart+1287}] [10037 10516] [10601 10672] [10733 10948] [11053 11100] [15815 15982] [30822 30833]")

grain_a = kgf.adaptive_grain(deband, 0.3)
grain_b = kgf.adaptive_grain(deband, 1)
grain_c = core.grain.Add(deband, var=3, uvar=0, constant=False) # Stylistic choice :^)
grain = fvf.rfs(grain_a, grain_b, mappings=f"[{opstart+1128} {opstart+1287}] [5494 5552] [10037 10199] [15815 15982] [24854 24931] [27697 27776]")
grain = fvf.rfs(grain, grain_c, mappings="[30822 30833]")


final = fvf.Depth(grain, 10)
final.set_output()