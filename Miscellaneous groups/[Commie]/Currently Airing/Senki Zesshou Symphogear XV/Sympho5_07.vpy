import vapoursynth as vs
import adjust
import fvsfunc as fvf
import kagefunc as kgf
import lvsfunc as lvf
core = vs.core


opstart, edstart = 4962-2396, 34045-2158

src = lvf.src(r'src/07/[HorribleSubs] Symphogear XV - 07 [1080p].mkv')
src = fvf.Depth(src, 16)


scaled = kgf.inverse_scale(src, height=872, kernel='bicubic', b=1/3, c=1/3, mask_detail=True, 
            descale_mask_zones=f"[{opstart} {opstart+2500}]")  # Also catch title after the OP
scaled = fvf.Depth(scaled, 16)
scaled = core.resize.Spline36(scaled, 1280, 720)


dim1 = adjust.Tweak(scaled, sat=1.35, cont=1.35)
dim2 = adjust.Tweak(scaled, sat=1.12, cont=1.12)
dim3 = adjust.Tweak(scaled, sat=1.15, cont=1.15)
dim4 = adjust.Tweak(scaled, sat=1.20, cont=1.20)
dim5 = adjust.Tweak(scaled, sat=4.50, cont=4.50)
dim6 = adjust.Tweak(scaled, sat=1.50, cont=1.50)
dim7 = adjust.Tweak(scaled, sat=1.10, cont=1.10)
dim8 = adjust.Tweak(scaled, sat=1.07, cont=1.07)
dim9 = adjust.Tweak(scaled, sat=1.03, cont=1.03)
undim = fvf.rfs(scaled, dim1, mappings=f"[{opstart+1616} {opstart+1659}]")
undim = fvf.rfs(undim, dim2, mappings=f"[{opstart+1665} {opstart+1693}] [{opstart+1937} {opstart+1964}] 8864")
undim = fvf.rfs(undim, dim3, mappings="6019 [8110 8115] [8120 8125] [8152 8155] [8269 8271] [8315 8325] [8399 8402] [8411 8428] [8499 8505] [8565 8571] [8599 8608] [8759 8863] [30462 30484] [30847 30860] [31272 31299]")
undim = fvf.rfs(undim, dim4, mappings="[8645 8650] [8653 8673] [30445 30461]")
undim = fvf.rfs(undim, dim5, mappings="8651")
undim = fvf.rfs(undim, dim6, mappings="8652")
undim = fvf.rfs(undim, dim7, mappings="8759 8864")
undim = fvf.rfs(undim, dim8, mappings="8865")
undim = fvf.rfs(undim, dim9, mappings="8866")


deblock = core.deblock.Deblock(undim, quant=15)

denoise = fvf.Depth(core.w2xc.Waifu2x(fvf.Depth(deblock, 32), noise=3, scale=1), 16)
denoise = fvf.rfs(deblock, denoise, mappings="8651")

deband_a = core.f3kdb.Deband(denoise, range=16, y=40, cb=32, cr=32, grainy=36, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(denoise, range=5, y=128, cb=120, cr=120, grainy=0, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(deband_b, range=21, y=64, cb=56, cr=56, grainy=48, grainc=0, output_depth=16)
deband = fvf.rfs(deband_a, deband_b, mappings="8651")

grain = kgf.adaptive_grain(deband, 0.3, luma_scaling=8)


out = grain
final = fvf.Depth(out, 10)
final.set_output()
