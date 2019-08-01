import vapoursynth as vs
import fvsfunc as fvf
import kagefunc as kgf
import lvsfunc as lvf
import mvsfunc as mvf
import vsTAAmbk as taa
from nnedi3_rpow2 import nnedi3_rpow2
core = vs.core

opstart = 2923-2156 # final frame of OP
edstart = 33085-2156 # final frame of ED

src_a = lvf.src(r"13/Demon Slayer Kimetsu no Yaiba E13 [1080p][AAC][JapDub][GerSub][Web-DL].mkv")
src_b = lvf.src(r"13/[APRZ] Kimetsu no Yaiba - 13 [1080p] [CR-DL] [Fix Version].mkv")
src_b = src_b[1:]
scomp = lvf.scomp(src_a, src_b, height=480)

hardsubmask = kgf.hardsubmask(src_a, src_b)
src = core.std.MaskedMerge(src_a, src_b, hardsubmask)

src_fade = fvf.Depth(kgf.hardsubmask_fades(src_a, src_b, highpass=1300), 8)
src_fade = core.std.MaskedMerge(src_a, src_b, src_fade)
src = fvf.ReplaceFramesSimple(src, src_fade, mappings=f"[{opstart+2156} {opstart+3500}]")

op = src_a[opstart:opstart+2156] # dehardsub kills the OP (thanks CR)
src = kgf.insert_clip(src, op, opstart)
src = fvf.Depth(src, 16)


Y, U, V = kgf.split(src)
descaled = kgf.inverse_scale(Y, height=855, kernel='bicubic', b=0.2, c=0.4, mask_detail=True)
descaled = fvf.Depth(descaled, 16)

aa_a = taa.TAAmbk(descaled, aatype='Nnedi3')
aa_b = taa.TAAmbk(descaled, aatype='Eedi3')
aa = fvf.rfs(aa_a, aa_b, mappings=f"[{opstart+292} {opstart+402}] [{opstart+1017} {opstart+1079}] [{opstart+1701} {opstart+1782}] [{opstart+1895} {opstart+1953}]")

scaled = nnedi3_rpow2(aa).resize.Spline36(1920, 1080)
scaled = kgf.join([scaled, U, V])


denoise = mvf.BM3D(scaled, sigma=[3,2])
deband_a = core.f3kdb.Deband(denoise, range=18, y=40, cb=32, cr=32, grainy=12, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(denoise, range=21, y=48, cb=40, cr=40, grainy=12, grainc=0, output_depth=16)
deband = fvf.rfs(deband_a, deband_b, mappings=f"[{opstart+1128} {opstart+1287}]")

grain_a = kgf.adaptive_grain(deband, 0.3)
grain_b = kgf.adaptive_grain(deband, 1)
grain = fvf.rfs(grain_a, grain_b, mappings=f"[{opstart+1128} {opstart+1287}]")


final = fvf.Depth(grain, 10)
final.set_output()
