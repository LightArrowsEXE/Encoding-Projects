import vapoursynth as vs
import adjust
import fvsfunc as fvf
import kagefunc as kgf
import lvsfunc as lvf
core = vs.core


opstart, edstart = 3668-2396, 34046-2159

src = lvf.src(r'src/05/[Erai-raws] Senki Zesshou Symphogear XV - 05 [1080p][Multiple Subtitle].mkv')
src = fvf.Depth(src, 16)


scaled = kgf.inverse_scale(src, height=871, kernel='bicubic', b=1/3, c=1/3, mask_detail=True, 
            descale_mask_zones=f"[{opstart} {opstart+3000}] [{edstart} {edstart+2159}]")  # Also catch title after the OP
scaled = fvf.Depth(scaled, 16)
scaled = core.resize.Spline36(scaled, 1280, 720)


dim1 = adjust.Tweak(scaled, sat=1.35, cont=1.35)
dim2 = adjust.Tweak(scaled, sat=1.12, cont=1.12)
dim3 = adjust.Tweak(scaled, sat=1.20, cont=1.20)
dim4 = adjust.Tweak(scaled, sat=1.40, cont=1.40)
undim = fvf.rfs(scaled, dim1, mappings=f"[{opstart+1613} {opstart+1659}]]")
undim = fvf.rfs(undim, dim2, mappings=f"[{opstart+1665} {opstart+1693}]")
undim = fvf.rfs(undim, dim3, mappings="[69 96] [165 184] [23298 23322]")
undim = fvf.rfs(undim, dim4, mappings="[9110 9269]")


deblock_a = core.deblock.Deblock(undim, quant=15)
deblock_b = core.deblock.Deblock(undim, quant=40)
deblock = fvf.rfs(deblock_a, deblock_b, mappings="")

denoise_b = fvf.Depth(core.w2xc.Waifu2x(fvf.Depth(undim, 32), noise=3, scale=1), 16)
denoise = fvf.rfs(deblock, denoise_b, mappings="")

deband_a = core.f3kdb.Deband(denoise, range=16, y=32, cb=24, cr=24, grainy=24, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(denoise, range=5, y=128, cb=120, cr=120, grainy=0, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(deband_b, range=18, y=64, cb=56, cr=56, grainy=48, grainc=0, output_depth=16)
deband = fvf.rfs(deband_a, deband_b, mappings="")

grain = kgf.adaptive_grain(deband, 0.3, luma_scaling=8)


out = grain
final = fvf.Depth(out, 10)
final.set_output()
