import vapoursynth as vs
import adjust
import fvsfunc as fvf
import kagefunc as kgf
import lvsfunc as lvf
from vsTAAmbk import TAAmbk
core = vs.core


opstart = 0

src = lvf.src(r'src/12/[Erai-raws] Senki Zesshou Symphogear XV - 12 [1080p][Multiple Subtitle].mkv')
src = fvf.Depth(src, 32)


b, c = 1/3, 1/3
scaled_OPED = kgf.inverse_scale(src, height=872, kernel='bicubic', b=b, c=c, mask_detail=True, 
            descale_mask_zones=f"[{opstart} {opstart+2500}] [31646 {src.num_frames-1}]").resize.Bicubic(1280, 720, filter_param_a=0, filter_param_b=1/2) # Also catch title after the OP
scaled_cond = lvf.conditional_descale(src, height=872, b=b, c=c, threshold=0.0012).resize.Bicubic(1280, 720, format=scaled_OPED.format, filter_param_a=0, filter_param_b=1/2)

scaled = fvf.rfs(scaled_OPED, scaled_cond, mappings=f"[{opstart} 2247] [31646 {src.num_frames-1}]")
scaled = fvf.Depth(scaled, 16)


# y'know, not having dimmed a single scene since like ep9 is starting to make me feel bad
dim1 = adjust.Tweak(scaled, sat=1.15, cont=1.15)
dim2 = adjust.Tweak(scaled, sat=1.35, cont=1.15)

undim = fvf.rfs(scaled, dim1, mappings="[13756 14203] [3776 6034] [7898 8022] [14687 14740] [15948 16019] [16074 16103] [16826 16840] [17259 17444] [17811 17861] [17976 18020] [18084 18137]")
undim = fvf.rfs(undim, dim2, mappings="[14443 14472]")


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
