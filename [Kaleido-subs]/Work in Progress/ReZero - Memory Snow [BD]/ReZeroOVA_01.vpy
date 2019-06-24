import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import vsTAAmbk as taa
import mvsfunc as mvf
import havsfunc as haf
core = vs.core
core.max_cache_size = 8192


src = lvf.src(r"REZERO_MEMORY_SNOW/BDMV/STREAM/00002.m2ts")
src = src[240:86559]
src = core.edgefixer.ContinuityFixer(src, [1,1,1], [1,1,1], [1,1,1], [1,1,1])
src = fvf.Depth(src, 16)


scaled_a = kgf.inverse_scale(src, height=720, kernel='bicubic', b=0, c=1/2)
scaled_a = fvf.Depth(scaled_a, 16)
scaled_b = core.resize.Spline36(src, 1280, 720, format=vs.YUV444P16)
scaled = fvf.rfs(scaled_a, scaled_b, mappings="[129 186] [335 450] [486 750] [985 1663] [4763 4882] [40632 40835] [81949 86318]")

denoise_a = mvf.BM3D(scaled, sigma=[1.4,0.2])
denoise_b = mvf.BM3D(scaled, sigma=[6,2])
denoise_c = mvf.BM3D(scaled, sigma=[3,0.6])
denoise = fvf.rfs(denoise_a, denoise_b, mappings="[4763 4882]")
denoise = fvf.rfs(denoise, denoise_c, mappings="[7979 8025] [12716 12832] [13802 13851] [14779 15315] [37034 37078] [44619 44699]")

aa_a = taa.TAAmbk(denoise, aatype='Nnedi3', cycle=1)
aa_b = taa.TAAmbk(denoise, aatype='Eedi3')
aa = fvf.rfs(aa_a, aa_b, mappings="[5011 5058] [8026 8084] [12886 13262] [27343 27581] [40080 40126] [40632 40835] [44114 44149] [49508 49536] [59978 60048]")

deband_a = core.f3kdb.Deband(aa, range=13, y=28, cb=20, cr=20, grainy=12, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(aa, range=5, y=64, cb=56, cr=56, grainy=0, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(deband_b, range=15, y=32, cb=24, cr=24, grainy=12, grainc=0, output_depth=16)
deband_c = core.f3kdb.Deband(aa, range=12, y=64, cb=56, cr=56, grainy=0, grainc=0, output_depth=16)
deband_c = core.f3kdb.Deband(deband_c, range=15, y=32, cb=24, cr=24, grainy=0, grainc=0, output_depth=16)
deband_d = core.f3kdb.Deband(aa, range=14, y=40, cb=32, cr=32, grainy=36, grainc=0, output_depth=16)
deband_e = core.f3kdb.Deband(aa, range=5, y=144, cb=136, cr=136, grainy=0, grainc=0, output_depth=16) # fuck fades
deband_e = core.f3kdb.Deband(deband_e, range=18, y=72, cb=64, cr=64, grainy=64, grainc=0, output_depth=16)
mask_a = kgf.adaptive_grain(scaled, show_mask=True, luma_scaling=134).std.Binarize().std.Invert()
mask_b = kgf.adaptive_grain(scaled, show_mask=True, luma_scaling=92).std.Binarize()
mask = core.std.Expr([mask_a, mask_b], expr="x y *") # wow this kinda worked
deband_f = core.std.MaskedMerge(deband_d, deband_e, mask)

deband = fvf.rfs(deband_a, deband_b, mappings="[4763 4882] [18448 18686] [22411 22506] [34799 34947]")
deband = fvf.rfs(deband, deband_c, mappings="[7979 8025] [13802 13851]")
deband = fvf.rfs(deband, deband_d, mappings="[12716 12832] [16920 17009] [23537 23579] [36932 37017] [37034 37078] [44619 44699] [60877 61001] [75367 75474]")
deband = fvf.rfs(deband, deband_e, mappings="[14779 15315] [73392 73501]")
deband = fvf.rfs(deband, deband_f, mappings="[22615 22677] [22809 23083] [23154 23267]")

grain_a = kgf.adaptive_grain(deband, 0.1)
grain_b = kgf.adaptive_grain(deband, 0.4, static=False)
grain = fvf.rfs(grain_a, grain_b, mappings="[14779 15315] [22615 22677] [22809 23083] [23154 23267]")


out = grain
final = fvf.Depth(out, 10)
final.set_output()