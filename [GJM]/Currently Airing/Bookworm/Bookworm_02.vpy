import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
from vsTAAmbk import TAAmbk
from vsutil import *
core = vs.core

opstart = 3548-2157


src = lvf.src(r'02/[Erai-raws] Honzuki no Gekokujou - Shisho ni Naru Tame ni wa Shudan wo Erandeiraremasen - 02 [1080p][Multiple Subtitle].mkv')
src = fvf.Depth(src, 32)

scaled = kgf.inverse_scale(src, height=812, 
                           kernel='bicubic', b=0, c=1/2, 
                           mask_detail=True) # Not 100% sure on this, but it works for now
scaled = core.resize.Spline36(scaled, get_w(810), 810)

denoise_a = core.knlm.KNLMeansCL(scaled, d=3, a=2, h=0.4)
denoise_b = core.knlm.KNLMeansCL(scaled, d=3, a=2, h=0.7)
denoise_c = core.knlm.KNLMeansCL(scaled, d=3, a=2, h=1)
denoise = fvf.rfs(denoise_a, denoise_b, mappings=f"[{opstart+246} {opstart+571}]")
denoise = fvf.rfs(denoise, denoise_c, mappings="")

aa = TAAmbk(fvf.Depth(denoise, 16), aatype='Nnedi3')

deband_a = core.f3kdb.Deband(aa, range=15, y=24, cb=16, cr=16, grainy=24, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(aa, range=20, y=56, cb=48, cr=48, grainy=48, grainc=0, output_depth=16)
deband_c = core.f3kdb.Deband(aa, range=18, y=40, cb=32, cr=32, grainy=36, grainc=0, output_depth=16)
deband = fvf.rfs(deband_a, deband_b, mappings=f"[{opstart+246} {opstart+571}]")
deband = fvf.rfs(deband, deband_c, mappings="")

grain_a = kgf.adaptive_grain(deband, 0.2, luma_scaling=10)
grain_b = kgf.adaptive_grain(deband, 0.4, luma_scaling=10)
grain = fvf.rfs(grain_a, grain_b, mappings="")


out = grain
final = fvf.Depth(out, 10)
final.set_output()
