import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import vsTAAmbk as taa
import mvsfunc as mvf
core = vs.core


src = lvf.src(r"G:/src/[Funimation] Fate Grand Order Zettai Majuu Sensen Babylonia - 00 [1080p].mkv")
src = src[289:]
src = fvf.Depth(src, 16)


denoise = mvf.BM3D(src, sigma=[2.5,1])
denoise = fvf.rfs(denoise, src, mappings="[4496 4537]")

mask = kgf.retinex_edgemask(core.dfttest.DFTTest(src, planes=0))
aa_a = taa.TAAmbk(denoise, aatype='Eedi3SangNom', sharp=120) # tfw SangNom still doesn't fix everything, even when not repairing
aa_b = taa.TAAmbk(denoise, aatype='Eedi3') # For scenes with credits
aa = fvf.rfs(aa_a, aa_b, mappings="[118 357] [466 555] [727 837] [969 1055] [1116 1247] [1286 1377] [1430 1522] [1720 1816] [2242 2359] [2387 2504] [2599 2682] [2724 2862] [3393 3476]")

deband = core.f3kdb.Deband(aa, range=17, y=32, cb=24, cr=24, grainy=12, grainc=0, output_depth=16)

merge = core.std.MaskedMerge(deband, aa, mask)

grain_a = kgf.adaptive_grain(merge, 0.4, luma_scaling=4)
sq_mask = kgf.squaremask(src, width=src.width, height=752, offset_x=0, offset_y=165)
grain_b = core.grain.Add(merge, var=3, uvar=0, constant=False)
grain_b = core.std.MaskedMerge(merge, grain_b, sq_mask)
grain_c = kgf.adaptive_grain(merge, 1, luma_scaling=2)
grain = fvf.rfs(grain_a, grain_b, mappings="[21535 22178]")
grain = fvf.rfs(grain, grain_c, mappings="[2505 2574]")

replace = fvf.rfs(grain, src, mappings="[35940 38105]")


out = replace
final = fvf.Depth(out, 10)
final.set_output()
