import vapoursynth as vs
import adjust
import fvsfunc as fvf
import kagefunc as kgf
import lvsfunc as lvf
from vsTAAmbk import TAAmbk
core = vs.core


opstart = 7959-2396

src = lvf.src(r'src/10/[Erai-raws] Senki Zesshou Symphogear XV - 10 [1080p][Multiple Subtitle].mkv')
src = fvf.Depth(src, 16)


scaled = kgf.inverse_scale(src, height=872, kernel='bicubic', b=1/3, c=1/3, mask_detail=True, 
            descale_mask_zones=f"[{opstart} {opstart+2500}] [31338 {src.num_frames-1}]")  # Also catch title after the OP
scaled = fvf.Depth(scaled, 16)
scaled = core.resize.Spline36(scaled, 1280, 720)


dim1 = adjust.Tweak(scaled, sat=1.35, cont=1.35)
dim2 = adjust.Tweak(scaled, sat=1.12, cont=1.12)
dim3 = adjust.Tweak(scaled, sat=1.05, cont=1.05)
dim4 = adjust.Tweak(scaled, sat=1.07, cont=1.07)
dim5 = adjust.Tweak(scaled, sat=1.30, cont=1.30)
dim6 = adjust.Tweak(scaled, sat=1.15, cont=1.15)
dim7 = adjust.Tweak(scaled, sat=1.15, cont=1.10)


undim = fvf.rfs(scaled, dim1, mappings=f"[{opstart+1616} {opstart+1659}] [26866 26919]")
undim = fvf.rfs(undim, dim2, mappings=f"[{opstart+1665} {opstart+1693}] [{opstart+1937} {opstart+1964}] [19747 19748]")
undim = fvf.rfs(undim, dim3, mappings="19745")
undim = fvf.rfs(undim, dim4, mappings="19746")
undim = fvf.rfs(undim, dim5, mappings="[19995 20010]")
undim = fvf.rfs(undim, dim6, mappings="[19749 19810] [19834 19870] [20016 20025] [20042 20044] [20063 20082]")
undim = fvf.rfs(undim, dim7, mappings="""[20576 20720] [20841 20900] [21577 21725] [22555 22672] [22736 22848] [23153 23154] [23188 23219] [23346 23362] 
                                         [25181 25249] [26416 26546] [26583 26628] [26770 26817] [27517 27740] [28272 28443] [28516 28586] [28947 29030]""")
# It may be undimmed, but at what cost?


denoise = fvf.Depth(core.w2xc.Waifu2x(fvf.Depth(undim, 32), noise=3, scale=1), 16)
denoise = fvf.rfs(undim, denoise, mappings="")

aa = TAAmbk(denoise, aatype='Nnedi3SangNom', sharp=120, repair=2)
aa = fvf.rfs(denoise, aa, mappings="")

deband_a = core.f3kdb.Deband(aa, range=16, y=40, cb=32, cr=32, grainy=36, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(aa, range=5, y=128, cb=120, cr=120, grainy=0, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(deband_b, range=21, y=64, cb=56, cr=56, grainy=48, grainc=0, output_depth=16)
deband = fvf.rfs(deband_a, deband_b, mappings="")

grain = kgf.adaptive_grain(deband, 0.3, luma_scaling=8)


out = grain
final = fvf.Depth(out, 10)
final.set_output()
