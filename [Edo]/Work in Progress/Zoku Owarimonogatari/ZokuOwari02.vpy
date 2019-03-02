import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import vsTAAmbk as taa
core = vs.core
core.max_cache_size = 8192

src = lvf.src(r"Zoku_Owarimonogatari\BDMV\STREAM\00002.m2ts")[24:35366]
scaled = kgf.inverse_scale(src, width=None, height=720, kernel='spline16', mask_detail=True, masking_areas=[[0,1415],[33184,35341]]).resize.Spline36(format=vs.YUV444P16)
scaled = core.edgefixer.ContinuityFixer(scaled, [2,2,2], [2,2,2], [2,2,2], [2,2,2], [10,5,5])

denoise = lvf.qden(scaled, h=0.4)
aa = taa.TAAmbk(scaled, aatype='Eedi3', opencl=True)

deband = core.f3kdb.Deband(denoise, range=18, y=56, cb=48, cr=48, grainy=12, grainc=0, output_depth=16)
op_deband = core.f3kdb.Deband(denoise, range=14, y=32, cb=24, cr=24, grainy=12, grainc=0, output_depth=16)
deband = fvf.rfs(deband, op_deband, mappings="[0 1415] [33184 35341]")

mask = kgf.retinex_edgemask(aa)
maskedmerge = core.std.MaskedMerge(deband, aa, mask)

up = nnedi3_rpow2(maskedmerge)
up = core.resize.Spline36(up, 1920, 1080)

grain = kgf.adaptive_grain(up, 0.3, luma_scaling=6)

out = grain
final = fvf.Depth(out, 10)
final.set_output()
