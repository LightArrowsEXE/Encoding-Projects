import vapoursynth as vs
import adjust
import fvsfunc as fvf
import kagefunc as kgf
import lvsfunc as lvf
core = vs.core


opstart, edstart = 4124-2396, 34047-2159

src = lvf.src(r'src/06/[Erai-raws] Senki Zesshou Symphogear XV - 06 [1080p][Multiple Subtitle].mkv')
src = fvf.Depth(src, 16)


scaled = kgf.inverse_scale(src, height=871, kernel='bicubic', b=1/3, c=1/3, mask_detail=True, 
            descale_mask_zones=f"[{opstart} {opstart+3000}] [{edstart} {edstart+2159}]")  # Also catch title after the OP
scaled = fvf.Depth(scaled, 16)
scaled = core.resize.Spline36(scaled, 1280, 720)


dim1 = adjust.Tweak(scaled, sat=1.35, cont=1.35)
dim2 = adjust.Tweak(scaled, sat=1.12, cont=1.12)
dim3 = adjust.Tweak(scaled, sat=1.50, cont=1.50)
dim4 = adjust.Tweak(scaled, sat=1.20, cont=1.20)
dim5 = adjust.Tweak(scaled, sat=1.15, cont=1.15)
dim6 = adjust.Tweak(scaled, sat=1.10, cont=1.10)
dim7 = adjust.Tweak(scaled, sat=1.05, cont=1.05)
dim8 = adjust.Tweak(scaled, sat=1.08, cont=1.08)
dim9 = adjust.Tweak(scaled, sat=1.06, cont=1.06)
dim10 = adjust.Tweak(scaled, sat=1.04, cont=1.04)
dim11 = adjust.Tweak(scaled, sat=1.02, cont=1.02)
undim = fvf.rfs(scaled, dim1, mappings=f"[{opstart+1614} {opstart+1657}]")
undim = fvf.rfs(undim, dim2, mappings=f"[{opstart+1663} {opstart+1691}] [{opstart+1935} {opstart+1962}]")
undim = fvf.rfs(undim, dim3, mappings="[24192 24218]")
undim = fvf.rfs(undim, dim4, mappings="[24219 24263] [24264 24325] [24359 24381] [24484 24498] [25957 26014] [26692 26723] 26740 26741 26744 26745 [26748 26799] [27839 27850]")
undim = fvf.rfs(undim, dim5, mappings="24382")
undim = fvf.rfs(undim, dim6, mappings="24383 [25567 25721] [25739 25790] [25791 25956] [26254 26283]")
undim = fvf.rfs(undim, dim7, mappings="24384")
undim = fvf.rfs(undim, dim8, mappings="25738")
undim = fvf.rfs(undim, dim9, mappings="25737")
undim = fvf.rfs(undim, dim10, mappings="25736")
undim = fvf.rfs(undim, dim11, mappings="25735")


deblock = core.deblock.Deblock(undim, quant=15)
deband = core.f3kdb.Deband(deblock, range=16, y=40, cb=32, cr=32, grainy=36, grainc=0, output_depth=16)
grain = kgf.adaptive_grain(deband, 0.3, luma_scaling=8)


out = grain
final = fvf.Depth(out, 10)
final.set_output()
