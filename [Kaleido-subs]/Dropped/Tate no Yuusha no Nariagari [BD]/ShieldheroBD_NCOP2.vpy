import vapoursynth as vs
import fvsfunc as fvf
import kagefunc as kgf
import lvsfunc as lvf
import mvsfunc as mvf
import vsTAAmbk as taa
core = vs.core

opstart, edstart = 0, None

src = lvf.src(r"BDMV/[BDMV][190524][Tate no Yuusha no Nariagari][Vol.2]/TATE_2_2/BDMV/STREAM/00012.m2ts")
src = src[24:2183]
src = fvf.Depth(src, 16)


mask = kgf.adaptive_grain(src, show_mask=True, luma_scaling=8)
denoise_a = mvf.BM3D(src, sigma=[3.5, 2])
denoise_b = mvf.BM3D(src, sigma=[2, 0.5])
denoise = core.std.MaskedMerge(denoise_a, denoise_b, mask)
#denoise = fvf.rfs(denoise, src, mappings="[{edstart} {edstart+2157}]")

aa = taa.TAAmbk(denoise, aatype='Nnedi3SangNom', sharp=120, repair=2)

deband_a = core.f3kdb.Deband(aa, range=15, y=24, cb=16, cr=16, grainy=0, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(aa, range=14, y=36, cb=24, cr=24, grainy=12, grainc=0, output_depth=16)
deband_c = core.f3kdb.Deband(aa, range=5, y=48, cb=40, cr=40, grainy=0, grainc=0, output_depth=16)
deband_c = core.f3kdb.Deband(deband_c, range=17, y=40, cb=32, cr=32, grainy=48, grainc=0, output_depth=16)
deband_d = core.f3kdb.Deband(aa, range=21, y=72, cb=64, cr=64, grainy=12, grainc=0, output_depth=16)
deband = core.std.MaskedMerge(deband_a, deband_b, mask)
deband = fvf.rfs(deband, deband_c, mappings="")
deband = fvf.rfs(deband, deband_d, mappings=f"[{opstart+487} {opstart+558}] [{opstart+958} {opstart+997}]")

grain_a = kgf.adaptive_grain(deband, 0.6, luma_scaling=8)
grain_b = kgf.adaptive_grain(deband, 3, static=False, luma_scaling=8)
grain = fvf.rfs(grain_a, grain_b, mappings=f"[{opstart+925} {opstart+1196}]")


out = grain
final = fvf.Depth(out, 10)
final.set_output()
