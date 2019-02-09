import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import vsTAAmbk as taa
core = vs.core

src = lvf.src(r"F:\Encode\Temp\A Certain Magical Index III E18 [CR-verison][1080p][AAC][JapDub][GerSub][Web-DL][.mkv")
src = src[2038:4197]
src = core.std.CropRel(src, 0, 0, 110, 110)
src = fvf.Depth(src, 16)

aa = taa.TAAmbk(src, aatype='Nnedi3')

mask = kgf.adaptive_grain(src, show_mask=True, luma_scaling=4)
deband_a = core.f3kdb.Deband(src, range=21, y=56, cb=48, cr=48, grainy=0, grainc=0, output_depth=16)
deband_a = core.std.MaskedMerge(src, deband_a, mask)

deband_b = lvf.denoise(src, h=2, sigma=7)
deband_b = core.f3kdb.Deband(deband_b, range=24, y=64, cb=56, cr=56, grainy=24, grainc=0, output_depth=16)
deband = fvf.rfs(deband_a, deband_b, mappings="[1322 1500]")

lmask = kgf.retinex_edgemask(src, 0.5).std.Binarize()
merge = core.std.MaskedMerge(deband, aa, lmask)

grain_a = kgf.adaptive_grain(merge, 1)
grain_b = core.grain.Add(merge, var=3, uvar=0, constant=False)
grain = fvf.rfs(grain_a, grain_b, mappings="[936 1125]")

out = grain
final = fvf.Depth(out, 10)
final.set_output()
