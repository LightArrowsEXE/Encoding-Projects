import vapoursynth as vs
import adjust
import fvsfunc as fvf
import kagefunc as kgf
import lvsfunc as lvf
from vsTAAmbk import TAAmbk
core = vs.core


opstart = 0

src = lvf.src(r'src/13/[HorribleSubs] Symphogear XV - 13 [1080p].mkv')
src = fvf.Depth(src, 32)


b, c = 1/3, 1/3
scaled = kgf.inverse_scale(src, height=872, kernel='bicubic', b=b, c=c, mask_detail=True, 
            descale_mask_zones=f"[{opstart} {opstart+1600}] [31646 {src.num_frames-1}]").resize.Bicubic(1280, 720, filter_param_a=0, filter_param_b=1/2) # Also catch title after the OP
scaled = fvf.Depth(scaled, 16)


dim1 = adjust.Tweak(scaled, sat=1.15, cont=1.15)
dim2 = adjust.Tweak(scaled, sat=1.20, cont=1.20)
dim3 = adjust.Tweak(scaled, sat=1.05, cont=1.05)
dim4 = adjust.Tweak(scaled, sat=1.10, cont=1.10)

undim = fvf.rfs(scaled, dim1, mappings="[1870 1938] [2011 2136] [2441 2670] [2719 2730] [5157 5697] [6482 6571] [6591 7079] [7140 7222] [7274 7842] [7961 7994] [8048 8244] [8634 8686] [9134 9178] [12581 13487] [14285 14862] [14898 15071] [22374 22527] [26853 26944] [27379 27920]")
undim = fvf.rfs(undim, dim2, mappings="[2731 2802] [2851 3108] [4444 4614] [4781 5156] [20144 20404]")
undim = fvf.rfs(undim, dim3, mappings="[3109 3147] [8771 8860] [13902 14284] [14863 14897] [25518 26047] [26437 26557] [26945 27053] [28077 29071]")
undim = fvf.rfs(undim, dim4, mappings="[13828 13901]")

sq_mask = kgf.squaremask(scaled, 712, 396, 0, 159)
ed_undim = fvf.rfs(undim, dim3, mappings="[32254 32305]")
undim = core.std.MaskedMerge(undim, ed_undim, sq_mask)


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
