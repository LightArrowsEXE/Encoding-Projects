import vapoursynth as vs
import adjust
import fvsfunc as fvf
import kagefunc as kgf
import lvsfunc as lvf
from vsTAAmbk import TAAmbk
core = vs.core


opstart = 4626-2396

src = lvf.src(r'src/08/[HorribleSubs] Symphogear XV - 08 [1080p].mkv')
src = fvf.Depth(src, 16)


scaled = kgf.inverse_scale(src, height=872, kernel='bicubic', b=1/3, c=1/3, mask_detail=True, 
            descale_mask_zones=f"[{opstart} {opstart+2500}] [31861 34045]")  # Also catch title after the OP
scaled = fvf.Depth(scaled, 16)
scaled = core.resize.Spline36(scaled, 1280, 720)


dim1 = adjust.Tweak(scaled, sat=1.35, cont=1.35)
dim2 = adjust.Tweak(scaled, sat=1.12, cont=1.12)
dim3 = adjust.Tweak(scaled, sat=1.15, cont=1.15)
dim4 = adjust.Tweak(scaled, sat=1.20, cont=1.20)
dim5 = adjust.Tweak(scaled, sat=1.25, cont=1.25)
dim6 = adjust.Tweak(scaled, sat=1.10, cont=1.10)
dim7 = adjust.Tweak(scaled, sat=1.30, cont=1.30)
dim8 = adjust.Tweak(scaled, sat=1.50, cont=1.50)
undim = fvf.rfs(scaled, dim1, mappings=f"[{opstart+1616} {opstart+1659}] ")
undim = fvf.rfs(undim, dim2, mappings=f"[{opstart+1665} {opstart+1693}] [{opstart+1937} {opstart+1964}]")
undim = fvf.rfs(undim, dim3, mappings="[1967 1994] [30154 30329]")
undim = fvf.rfs(undim, dim4, mappings="[1551 1568] [8298 8410] [19011 19099] [19294 19780] [25532 25580] [28051 28231] [28374 28553]")
undim = fvf.rfs(undim, dim5, mappings="[5424 5549] [20696 20722] [20971 21037]")
undim = fvf.rfs(undim, dim6, mappings="[5925 5955] [8411 8487] [21832 21971] [22533 22578] [22704 22778] [25419 25494] [25933 25962] [26047 26107] [28274 28348] [28620 28643] [28889 28907] [31472 31493]")
undim = fvf.rfs(undim, dim7, mappings="[8053 8116] [26108 26204]")
undim = fvf.rfs(undim, dim8, mappings="[28349 28354]")

undim = kgf.insert_clip(undim, undim[28357], 28356)

denoise = fvf.Depth(core.w2xc.Waifu2x(fvf.Depth(undim, 32), noise=3, scale=1), 16)
denoise = fvf.rfs(undim, denoise, mappings="")

aa = TAAmbk(denoise, aatype='Nnedi3SangNom', sharp=120, repair=2)
aa = fvf.rfs(denoise, aa, mappings="[14700 14713]")

deband_a = core.f3kdb.Deband(aa, range=16, y=40, cb=32, cr=32, grainy=36, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(aa, range=5, y=128, cb=120, cr=120, grainy=0, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(deband_b, range=21, y=64, cb=56, cr=56, grainy=48, grainc=0, output_depth=16)
deband = fvf.rfs(deband_a, deband_b, mappings="")

grain = kgf.adaptive_grain(deband, 0.3, luma_scaling=8)


out = grain
final = fvf.Depth(out, 10)
final.set_output()
