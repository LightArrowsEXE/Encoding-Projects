import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
from vsutil import *
from vsTAAmbk import *
core = vs.core

opstart, edstart = 3020-2157, 31049


src = lvf.src(r'12/[Erai-raws] Honzuki no Gekokujou - Shisho ni Naru Tame ni wa Shudan wo Erandeiraremasen - 12 [1080p][Multiple Subtitle].mkv')
src = core.std.AssumeFPS(src, fpsnum=24000, fpsden=1001)
src = fvf.Depth(src, 32)

planes = split(src)
planes[0] = kgf.inverse_scale(planes[0], height=812,
                           kernel='bicubic', b=0, c=1/2,
                           mask_detail=True, # Not 100% sure on this, but it works for now
                           descale_mask_zones=f"[{opstart} {opstart+2400}] [{edstart-84} {src.num_frames-1}]")
planes[0] = core.resize.Bilinear(planes[0], get_w(810), 810)
planes[1], planes[2] = [core.resize.Bicubic(p, planes[0].width, planes[0].height, format=planes[0].format, src_left=.25) for p in planes[1:]]
scaled = join(planes)
scaled = fvf.Depth(scaled, 16)


#denoise_a = core.knlm.KNLMeansCL(scaled, h=0.5)
#denoise_b = core.knlm.KNLMeansCL(scaled, d=3, a=2, h=1)
# NOTE: Replace with old denoising for future encodes
d_mask = kgf.adaptive_grain(fvf.Depth(scaled, 16), show_mask=True, luma_scaling=6)
denoise_a = mvf.BM3D(scaled, sigma=0.2, depth=16) 
denoise_b = mvf.BM3D(scaled, sigma=0.5, depth=16) 
denoise_c = mvf.BM3D(scaled, sigma=1.5, radius1=2, depth=16)
denoise = core.std.MaskedMerge(denoise_a, denoise_b, d_mask)
denoise = fvf.rfs(denoise, denoise_c, mappings=f"[{opstart+246} {opstart+571}]")
aa = TAAmbk(denoise, aatype='Nnedi3')

deband_a = core.f3kdb.Deband(aa, range=15, y=24, cb=16, cr=16, grainy=24, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(aa, range=20, y=56, cb=48, cr=48, grainy=48, grainc=0, output_depth=16)
deband = fvf.rfs(deband_a, deband_b, mappings=f"[{opstart+246} {opstart+571}]")

grain = kgf.adaptive_grain(deband, 0.2, luma_scaling=10)


out = grain
final = fvf.Depth(out, 10)
final.set_output()
