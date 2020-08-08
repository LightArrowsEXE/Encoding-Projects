import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
from cooldegrain import *
core = vs.core


src = lvf.src('00/[Erai-raws] Fate Grand Order - Zettai Majuu Sensen Babylonia - Initium Iter - 00 [1080p][Multiple Subtitle].mkv')
src = fvf.Depth(src, 16)

# Generic filterchain
y, u, v = kgf.split(src)
aa = lvf.upscaled_sraa(y)
aa = kgf.join([aa, u, v])

d_mask = kgf.adaptive_grain(fvf.Depth(src, 16), show_mask=True, luma_scaling=6)
denoise_a = CoolDegrain(aa, tr=1, thsad=72, thsadc=48, bits=16, blksize=8, overlap=4)
denoise_b = CoolDegrain(aa, tr=1, thsad=24, thsadc=48, bits=16, blksize=8, overlap=4)
denoise = core.std.MaskedMerge(denoise_a, denoise_b, d_mask)

deband = core.f3kdb.Deband(denoise, range=17, y=32, cb=24, cr=24, grainy=48, grainc=0, output_depth=16)

sqmask = kgf.squaremask(fvf.Depth(src, 16), 1920, 752, 0, 165)
grain_a = kgf.adaptive_grain(deband, 0.2, luma_scaling=6)
grain_b = core.grain.Add(deband, 10, constant=True)
grain_b = core.std.MaskedMerge(deband, grain_b, sqmask)
grain = fvf.rfs(grain_a, grain_b, mappings="[21536 22177]")


out = grain
final = fvf.Depth(out, 10)
final.set_output()
