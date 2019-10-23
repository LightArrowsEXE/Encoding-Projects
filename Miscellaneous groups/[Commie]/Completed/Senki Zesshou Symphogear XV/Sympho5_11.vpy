import vapoursynth as vs
import adjust
import fvsfunc as fvf
import kagefunc as kgf
import lvsfunc as lvf
from vsTAAmbk import TAAmbk
core = vs.core


opstart = 5777-2396

src = lvf.src(r'src/11/[Erai-raws] Senki Zesshou Symphogear XV - 11 [1080p][Multiple Subtitle].mkv')
src = fvf.Depth(src, 32)


b, c = 1/3, 1/3
scaled_OPED = kgf.inverse_scale(src, height=872, kernel='bicubic', b=b, c=c, mask_detail=True, 
            descale_mask_zones=f"[{opstart} {opstart+2500}] [31888 {src.num_frames-1}]").resize.Bicubic(1280, 720, filter_param_a=0, filter_param_b=1/2) # Also catch title after the OP
scaled_cond = lvf.conditional_descale(src, height=872, b=b, c=c, threshold=0.0012).resize.Bicubic(1280, 720, format=scaled_OPED.format, filter_param_a=0, filter_param_b=1/2)

scaled = fvf.rfs(scaled_OPED, scaled_cond, mappings=f"[{opstart} 5996] [16358 16626] [31888 {src.num_frames-1}]")
scaled = fvf.Depth(scaled, 16)


# tfw louis is slowly getting killed with undimming :notlikemiya:
dim1 = adjust.Tweak(scaled, sat=1.35, cont=1.35)
dim2 = adjust.Tweak(scaled, sat=1.12, cont=1.12)
dim3 = adjust.Tweak(scaled, sat=1.15, cont=1.15)
dim4 = adjust.Tweak(scaled, sat=1.40, cont=1.40)
dim5 = adjust.Tweak(scaled, sat=1.30, cont=1.30)
dim6 = adjust.Tweak(scaled, sat=1.05, cont=1.05)

undim = fvf.rfs(scaled, dim1, mappings=f"[{opstart+1616} {opstart+1659}] [26866 26919]")
undim = fvf.rfs(undim, dim2, mappings=f"[{opstart+1665} {opstart+1693}] [{opstart+1937} {opstart+1964}]")
undim = fvf.rfs(undim, dim3, mappings="[1204 1361] [10977 11009] [11327 11339] [11341 11363] [24393 24398] [24564 24567] [24603 24604] [24616 24627] [24656 24657] [24684 24686] [24695 24696] [29425 29525] [29905 29993]")
undim = fvf.rfs(undim, dim4, mappings="[10908 10976] [11028 11042] [11045 11086] [11104 11225] 11340 [29133 29210]")
undim = fvf.rfs(undim, dim5, mappings="[11291 11308] [24379 24392]")
undim = fvf.rfs(undim, dim6, mappings="[11325 11326] [11364 11365]")


denoise = fvf.Depth(core.w2xc.Waifu2x(fvf.Depth(undim, 32), noise=3, scale=1), 16)
denoise = fvf.rfs(undim, denoise, mappings="")

aa = TAAmbk(denoise, aatype='Nnedi3SangNom', sharp=120, repair=2)
aa = fvf.rfs(denoise, aa, mappings="")

deband_a = core.f3kdb.Deband(aa, range=17, y=40, cb=32, cr=32, grainy=32, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(aa, range=5, y=128, cb=120, cr=120, grainy=0, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(deband_b, range=21, y=64, cb=56, cr=56, grainy=48, grainc=0, output_depth=16)
deband = fvf.rfs(deband_a, deband_b, mappings="")

grain = kgf.adaptive_grain(deband, 0.3, luma_scaling=8)


out = grain
final = fvf.Depth(out, 10)
final.set_output()
