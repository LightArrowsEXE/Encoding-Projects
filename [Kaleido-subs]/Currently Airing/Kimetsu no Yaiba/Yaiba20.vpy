import vapoursynth as vs
import fvsfunc as fvf
import kagefunc as kgf
import lvsfunc as lvf
import mvsfunc as mvf
import vsTAAmbk as taa
from nnedi3_rpow2 import nnedi3_rpow2
core = vs.core

opstart, edstart = 2756-2156, 33084-2156

src_a = lvf.src(r"20/Demon Slayer Kimetsu no Yaiba E20 [1080p][AAC][JapDub][GerSub][Web-DL].mkv")
src_b = lvf.src(r"20/[Erai-raws] Kimetsu no Yaiba - 20 [1080p][Multiple Subtitle].mkv")
src_b = src_b[1:]
scomp = lvf.scomp(src_a, src_b, height=480) # Matching

hardsubmask = kgf.hardsubmask(src_a, src_b)
src = core.std.MaskedMerge(src_a, src_b, hardsubmask)

src_fade = fvf.Depth(kgf.hardsubmask_fades(src_a, src_b, highpass=1300), 8)
src_fade = core.std.MaskedMerge(src_a, src_b, src_fade)
src = fvf.ReplaceFramesSimple(src, src_fade, mappings=f"[{opstart+2156} {opstart+3500}] [{edstart} {edstart+2156}] [15548 15703] [20797 20868]")

op = src_a[opstart:opstart+2156] # dehardsub kills the OP (thanks CR)
src = kgf.insert_clip(src, op, opstart)
src = fvf.Depth(src, 16)


Y, U, V = kgf.split(src)
descaled = kgf.inverse_scale(Y, height=855, kernel='bicubic', b=0.2, c=0.4, mask_detail=True, descale_mask_zones=f"[{opstart} {opstart+2156}]")
descaled = fvf.Depth(descaled, 16)

aa_a = taa.TAAmbk(descaled, aatype='Nnedi3')
aa_b = taa.TAAmbk(descaled, aatype='Eedi3')
aa = fvf.rfs(aa_a, aa_b, mappings=f"[{opstart+292} {opstart+402}] [{opstart+1017} {opstart+1079}] [{opstart+1701} {opstart+1782}] [{opstart+1895} {opstart+1953}] [65 178] 247 545 [3141 3188] [5180 5796] [6313 6339] [6571 6734] [7009 7046] [7785 7874] [8404 8450] [10888 10926] [10982 10983] [12372 12419] [15473 15848] [18083 18334] [18713 19024] [19738 19803] [25243 25458]")

scaled = nnedi3_rpow2(aa).resize.Spline36(1920, 1080)
scaled = kgf.join([scaled, U, V])
scaled = fvf.rfs(scaled, src, mappings="[30929 33084]") # Ep19 ED


denoise = mvf.BM3D(scaled, sigma=[3,2])
denoise = fvf.rfs(denoise, scaled, mappings="[30929 33084]")

deband_a = core.f3kdb.Deband(denoise, range=18, y=40, cb=32, cr=32, grainy=12, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(denoise, range=21, y=48, cb=40, cr=40, grainy=12, grainc=0, output_depth=16)
deband = fvf.rfs(deband_a, deband_b, mappings=f"[{opstart+1128} {opstart+1287}] [25565 25718] [30660 30813]")
deband = fvf.rfs(deband, scaled, mappings="[14891 14974]")

grain_a = kgf.adaptive_grain(deband, 0.3)
grain_b = kgf.adaptive_grain(deband, 1)
grain = fvf.rfs(grain_a, grain_b, mappings=f"[{opstart+1128} {opstart+1287}] [12156 15268] [15921 17254] [25565 25718]")


final = fvf.Depth(grain, 10)
final.set_output()