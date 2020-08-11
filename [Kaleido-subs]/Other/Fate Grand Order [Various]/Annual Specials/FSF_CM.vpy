import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import mvsfunc as mvf
import havsfunc as haf
from vsutil import *
from vsTAAmbk import *
core = vs.core


src_a, src_b = lvf.src(r'src/1912312200_【ＢＳ１１イレブン】Fate Project 大晦日TVスペシャル 2019【BS11 大晦日超アニメスペシャル！】.d2v'), lvf.src(r'Anniversaries/src/_-yHmQsWyCP3Q.mp4')
src_a = lvf.decomb(src_a, True)[80566:81285]
src = src_a[:672]+src_b[665:]

blank = core.std.BlankClip(src)
sqmask = kgf.squaremask(src, 1920, 128, 0, 0)
src_c = core.std.MaskedMerge(src, blank, sqmask)

src = fvf.rfs(src, src_c, mappings="[0 671]")
src = fvf.Depth(src, 32)

planes = split(src)
planes[0] = lvf.upscaled_sraa(planes[0], h=720, rfactor=3)
planes[1], planes[2] = [core.resize.Bicubic(p, planes[0].width, planes[0].height) for p in planes[1:]]
scaled = join(planes)

aa = TAAmbk(fvf.Depth(scaled, 16), aatype='Eedi3', repair=2)
darken = haf.FastLineDarkenMOD(aa, strength=12, protection=5, luma_cap=191, threshold=4, thinning=0)
l_mask = kgf.retinex_edgemask(darken)


d_mask = kgf.adaptive_grain(fvf.Depth(scaled, 16), show_mask=True, luma_scaling=8)
denoise_a = mvf.BM3D(scaled, sigma=[1.2,1], depth=16, profile1='lc')
denoise_b = mvf.BM3D(scaled, sigma=[.9,.5], depth=16, profile1='lc')
denoise = core.std.MaskedMerge(denoise_a, denoise_b, d_mask)

deband_a = core.f3kdb.Deband(denoise, range=15, y=32, cb=24, cr=24, grainy=12, grainc=0, output_depth=16)
deband_a = core.std.MaskedMerge(deband_a, darken, l_mask)
deband_b = core.f3kdb.Deband(aa, range=17, y=32, cb=32, cr=32, grainy=0, grainc=0, output_depth=16)
deband = fvf.rfs(deband_a, deband_b, mappings="[672 726]")

grain = kgf.adaptive_grain(deband, 0.1, luma_scaling=6)


out = grain
final = fvf.Depth(out, 10)
final.set_output()
