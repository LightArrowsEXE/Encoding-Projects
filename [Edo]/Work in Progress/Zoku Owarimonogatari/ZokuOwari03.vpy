import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import vsTAAmbk as taa
core = vs.core
core.max_cache_size = 8192

src = lvf.src(r"Zoku_Owarimonogatari\BDMV\STREAM\00003.m2ts")[24:37523]
scaled = kgf.inverse_scale(src, width=None, height=720, kernel='spline16', mask_detail=True, masking_areas=[[8942,10381],[35341,37498]]).resize.Spline36(format=vs.YUV444P16)
scaled = core.edgefixer.ContinuityFixer(scaled, [2,2,2], [2,2,2], [2,2,2], [2,2,2], [10,5,5])

denoise = lvf.qden(scaled, h=0.4)
aa = taa.TAAmbk(scaled, aatype='Eedi3', opencl=True)

deband_a = core.f3kdb.Deband(denoise, range=18, y=56, cb=48, cr=48, grainy=12, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(denoise, range=21, y=56, cb=48, cr=48, grainy=36, grainc=0, output_depth=16)
deband_c = core.f3kdb.Deband(denoise, range=13, y=80, cb=72, cr=72, grainy=0, grainc=0, output_depth=16)
deband_c = core.f3kdb.Deband(deband_c, range=14, y=48, cb=40, cr=40, grainy=36, grainc=0, output_depth=16)
op_deband = core.f3kdb.Deband(denoise, range=14, y=32, cb=24, cr=24, grainy=12, grainc=0, output_depth=16)
deband = fvf.rfs(deband_a, deband_b, mappings="[7953 7991] [8073 8272]")
deband = fvf.rfs(deband, deband_c, mappings="[7992 8072]") # holy shit the banding. If you scenefilter this seriously, custom mask this.
deband = fvf.rfs(deband, op_deband, mappings="[8942 10381] [35341 37498]")

mask = kgf.retinex_edgemask(aa)
maskedmerge = core.std.MaskedMerge(deband, aa, mask)

up = nnedi3_rpow2(maskedmerge)
up = core.resize.Spline36(up, 1920, 1080)

grain = kgf.adaptive_grain(up, 0.3, luma_scaling=6)

out = grain
final = fvf.Depth(out, 10)
final.set_output()
