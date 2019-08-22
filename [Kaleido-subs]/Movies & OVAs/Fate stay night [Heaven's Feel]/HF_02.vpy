import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import mvsfunc as mvf
import vsTAAmbk as taa
core = vs.core


src_a = lvf.src(r'G:\src\FateHF2\BDMV\STREAM\00000.m2ts')
src_b = lvf.src(r'G:\src\FateHF2\BDMV\STREAM\00001.m2ts')
src = src_a+src_b # why would they split this up reeeeee


scaled_b = core.resize.Bicubic(src, 1520, 855, format=vs.YUV444P16)
scaled_a = kgf.inverse_scale(src, height=855, kernel='bicubic', b=1/5, c=2/5, mask_detail=True, 
            descale_mask_zones="[6511 8603]") # Not re-upscaling. A true meme release must use a meme resolution.
scaled_a = fvf.Depth(scaled_a, 16) # reeeeeee kageru
scaled = fvf.rfs(scaled_a, scaled_b, mappings="[0 512] [160127 166650] [166994 167037] [167085 167145] [167193 167247] [167292 167342] [167471 167710] [168191 168503]")

mask = kgf.adaptive_grain(scaled_b, show_mask=True, luma_scaling=8)
denoise_a = mvf.BM3D(scaled, sigma=[2,1])
denoise_a = core.std.MaskedMerge(scaled, denoise_a, mask)
denoise_b = mvf.BM3D(scaled, sigma=[4,2])
denoise = fvf.rfs(denoise_a, denoise_b, mappings="[81707 81754] [152775 152854]")

aa = taa.TAAmbk(denoise, aatype='Eedi3')

deband_a = core.f3kdb.Deband(aa, range=16, y=40, cb=32, cr=32, grainy=48, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(aa, range=7, y=72, cb=64, cr=64, grainy=0, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(deband_b, range=16, y=40, cb=32, cr=32, grainy=48, grainc=0, output_depth=16)
deband_c = core.f3kdb.Deband(aa, range=5, y=40, cb=32, cr=32, grainy=0, grainc=0, output_depth=16)
deband_c = core.f3kdb.Deband(deband_c, range=21, y=48, cb=40, cr=40, grainy=48, grainc=0, output_depth=16)
deband_d = core.f3kdb.Deband(aa, range=21, y=48, cb=40, cr=40, grainy=48, grainc=0, output_depth=16)
deband = fvf.rfs(deband_a, deband_b, mappings="[81707 81754]")
deband = fvf.rfs(deband, deband_c, mappings="[152775 152854]")
deband = fvf.rfs(deband, deband_d, mappings="[154795 155070]")

grain_a = kgf.adaptive_grain(deband, 0.5, luma_scaling=8)
grain_b = core.grain.Add(deband, var=3, uvar=0)
grain = fvf.rfs(grain_a, grain_b, mappings="[81707 81754]")


out = grain
final = fvf.Depth(out, 10)
comp = lvf.comp(src, out, [167085])
src.set_output()
