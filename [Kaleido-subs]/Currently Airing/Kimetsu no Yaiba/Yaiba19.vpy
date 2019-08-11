import vapoursynth as vs
import fvsfunc as fvf
import kagefunc as kgf
import lvsfunc as lvf
import mvsfunc as mvf
import vsTAAmbk as taa
from nnedi3_rpow2 import nnedi3_rpow2
core = vs.core

opstart, edstart = 2804-2156, 30929

src_a = lvf.src(r"19/Demon Slayer Kimetsu no Yaiba E19 [1080p][AAC][JapDub][GerSub][Web-DL].mkv")
src_b = lvf.src(r"19/[Erai-raws] Kimetsu no Yaiba - 19 [1080p][Multiple Subtitle].mkv")
src_b = src_b[1:]
scomp = lvf.scomp(src_a, src_b, height=480) # Matching

hardsubmask = kgf.hardsubmask(src_a, src_b)
src = core.std.MaskedMerge(src_a, src_b, hardsubmask)

src_fade = fvf.Depth(kgf.hardsubmask_fades(src_a, src_b, highpass=1300), 8)
src_fade = core.std.MaskedMerge(src_a, src_b, src_fade)
src = fvf.ReplaceFramesSimple(src, src_fade, mappings=f"[{opstart+2156} {opstart+3500}] [15548 15703] [20797 20868]")

op = src_a[opstart:opstart+2156] # dehardsub kills the OP (thanks CR)
src = kgf.insert_clip(src, op, opstart)
src = fvf.Depth(src, 16)


Y, U, V = kgf.split(src)
descaled = kgf.inverse_scale(Y, height=855, kernel='bicubic', b=0.2, c=0.4, mask_detail=True, descale_mask_zones=f"[{opstart} {opstart+2156}]")
descaled = fvf.Depth(descaled, 16)

aa_a = taa.TAAmbk(descaled, aatype='Nnedi3')
aa_b = taa.TAAmbk(descaled, aatype='Eedi3')
aa = fvf.rfs(aa_a, aa_b, mappings=f"[{opstart+292} {opstart+402}] [{opstart+1017} {opstart+1079}] [{opstart+1701} {opstart+1782}] [{opstart+1895} {opstart+1953}] [0 36] [5649 5726] [6311 6634] [7431 7514] [8451 8470] [8597 8633] [8728 8863] [9134 9265] [9314 9463] [9548 9574] [11360 11456] [17739 17869] [17930 18065] [18101 18212] [18315 18357] [18408 18428] [18479 18520] [18607 18654] [18703 18894] [19478 19601] [20546 20572] [21270 21386] [21860 21975] [22054 22095] [22508 22579] [22730 22927] [23209 23299] [23322 23365] [23585 23644] [23873 24008] [24081 24408] [27914 28577] [28650 28807] [28826 29057] [29118 29296] [29501 29650] [29933 30172] [30268 30270] [30285 30313] 30378 30411")

scaled = nnedi3_rpow2(aa).resize.Spline36(1920, 1080)
scaled = kgf.join([scaled, U, V])
scaled = fvf.rfs(scaled, src, mappings="[30929 33084]") # Ep19 ED


denoise = mvf.BM3D(scaled, sigma=[3,2])
denoise = fvf.rfs(denoise, scaled, mappings="[30929 33084]")

deband_a = core.f3kdb.Deband(denoise, range=18, y=40, cb=32, cr=32, grainy=12, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(denoise, range=21, y=48, cb=40, cr=40, grainy=12, grainc=0, output_depth=16)
deband = fvf.rfs(deband_a, deband_b, mappings=f"[{opstart+1128} {opstart+1287}]")

grain_a = kgf.adaptive_grain(deband, 0.3)
grain_b = kgf.adaptive_grain(deband, 1)
grain_c = core.grain.Add(deband, var=3, uvar=0, constant=False) # Stylistic choice :^)
grain = fvf.rfs(grain_a, grain_b, mappings=f"[{opstart+1128} {opstart+1287}] [30173 30928]")
grain = fvf.rfs(grain, grain_c, mappings="[25 36]")


final = fvf.Depth(grain, 10)
final.set_output()