import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import vsTAAmbk as taa
from nnedi3_rpow2 import nnedi3_rpow2
core = vs.core
core.max_cache_size = 8192

opstart = 816
edstart = 33085-2156

src_a = lvf.src(r"03/Demon Slayer Kimetsu no Yaiba E03 [1080p][AAC][JapDub][GerSub][Web-DL].mp4")
src_b = lvf.src(r"03/[Erai-raws] Kimetsu no Yaiba - 03 [1080p][Multiple Subtitle].mkv")
#src_b = src_b[1:]
scomp = lvf.scomp(src_a, src_b, height=480)

hardsubmask = kgf.hardsubmask(src_a, src_b)
src = core.std.MaskedMerge(src_a, src_b, hardsubmask)

src_fade = fvf.Depth(kgf.hardsubmask_fades(src_a, src_b, highpass=1300), 8)
src_fade = core.std.MaskedMerge(src_a, src_b, src_fade)
src = fvf.ReplaceFramesSimple(src, src_fade, mappings=f"[4761 4904]")

# Splice in OP because dehardsubbing stinx
src_a_OP = src_a[opstart:opstart+2156]
src = kgf.insert_clip(src, src_a_OP, opstart)
src = fvf.Depth(src, 16)
Y, U, V = kgf.split(src)

scaled = kgf.inverse_scale(src, height=855, kernel='bicubic', a1=1/5, a2=4/10, mask_detail=True, masking_areas=[[opstart,opstart+1000],[edstart,edstart+2156]])
scaled = fvf.Depth(scaled, 16)
Y2, U2, V2 = kgf.split(scaled)
aa = taa.TAAmbk(Y2, aatype='Nnedi3')
scaled = nnedi3_rpow2(aa).resize.Spline36(1920, 1080)
scaled = kgf.join([scaled, U, V])


denoise = lvf.quick_denoise(scaled, h=0.4, sigma=4)
deband = core.f3kdb.Deband(denoise, range=18, y=40, cb=32, cr=32, grainy=12, grainc=0, output_depth=16)
grain = kgf.adaptive_grain(deband, 0.3)


# # # # OP FILTERING # # # #
op_aa = taa.TAAmbk(scaled, aatype='Eedi3', opencl=True)
op_aa = fvf.rfs(scaled, op_aa, mappings=f"[{opstart+292} {opstart+402}] [{opstart+1017} {opstart+1079}] [{opstart+1701} {opstart+1782}][{opstart+1895} {opstart+1953}]")

op_denoise = lvf.quick_denoise(op_aa, h=0.8, sigma=4)
op_denoise = fvf.rfs(op_aa, op_denoise, mappings=f"[{opstart} {opstart+404}] [{opstart+1017} {opstart+1079}] [{opstart+1128} {opstart+1287}] [{opstart+1320} {opstart+1398}]")

op_deband_a = core.f3kdb.Deband(op_denoise, range=18, y=40, cb=32, cr=32, grainy=12, grainc=0, output_depth=16)
op_deband_b = core.f3kdb.Deband(op_denoise, range=21, y=48, cb=40, cr=40, grainy=12, grainc=0, output_depth=16)
op_deband = fvf.rfs(op_deband_a, op_deband_b, mappings=f"[{opstart+1128} {opstart+1287}]")

op_grain_a = kgf.adaptive_grain(op_deband, 0.3)
op_grain_b = kgf.adaptive_grain(op_deband, 1)
op_grain = fvf.rfs(op_grain_a, op_grain_b, mappings=f"[{opstart+1128} {opstart+1287}]")
# # # # OP FILTERING # # # #


ep_out = grain
op_out = op_grain

merge = fvf.rfs(ep_out, op_out, f"[{opstart} {opstart+2156}]")

final = fvf.Depth(merge, 10)
final.set_output()
