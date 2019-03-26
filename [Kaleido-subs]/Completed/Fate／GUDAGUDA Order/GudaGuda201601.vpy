import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import vsTAAmbk as taa
core = vs.core
core.max_cache_size = 8192

"""
    Subtitle Source: 
    https://www.youtube.com/watch?v=kSdv9S-VTjk
"""

"""
    Cut Audio:
        Part A: 141878-144303
        Part B: 151728-154006
        Part C: 170858-172204
        Part D: 180778-182666
        Part E: 200085-202902
"""

src = lvf.src(r"TV caps/Fate／Grand Order -First Order- Fate Project 大晦日TVスペシャル ～First & Next Order～ (BS11).ts.d2v")
src = fvf.AutoDeblock(src)
src = core.edgefixer.ContinuityFixer(src, [6,3,3], [6,3,3], [6,3,3], [6,3,3], [10,5,5])
src = fvf.Depth(src, 16)

c0 = fvf.JIVTC(src, 0, draft=False, thr=15)
c3 = fvf.JIVTC(src, 3, draft=False, thr=15)
c4 = fvf.JIVTC(src, 4, draft=False, thr=15)

src = c4[113502:115443]+c4[121382:123205]+c0[136687:137764]+c3[144623]+c3[144623:146133]+c3[160068:162322]

scaled = core.resize.Spline36(src, 1280, 720)

denoised = lvf.qden(scaled, h=1.4, sigma=6)
denoised = fvf.rfs(scaled, denoised, mappings="[3938 4017] [4060 4270]")
deband_a = core.f3kdb.Deband(denoised, range=14, y=32, cb=24, cr=24, grainy=0, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(denoised, range=21, y=64, cb=56, cr=56, grainy=0, grainc=0, output_depth=16)
deband = fvf.rfs(deband_a, deband_b, mappings="[8306 8523]")

aa = taa.TAAmbk(scaled, aatype='Eedi3')

mask = kgf.retinex_edgemask(scaled)
maskedmerge = core.std.MaskedMerge(deband, aa, mask)

grain = kgf.adaptive_grain(maskedmerge, 1)
grain = fvf.rfs(maskedmerge, grain, mappings="[8306 8523]")

out = grain
final = fvf.Depth(out, 10)
final.set_output()
