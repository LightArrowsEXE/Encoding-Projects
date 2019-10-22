import vapoursynth as vs
import fvsfunc as fvf
import kagefunc as kgf
import lvsfunc as lvf
import mvsfunc as mvf
from cooldegrain import *
from nnedi3_rpow2 import *
from vsutil import get_w, get_y, split, join
core = vs.core

opstart, edstart = None, 0


src = lvf.src(r"BDMV/[BDMV][190731][Kimetsu no Yaiba][Vol.1]/BDMV/STREAM/00008.m2ts")
src = src[:-24]
src = fvf.Depth(src, 16)


b, c = 1/5, 2/5
y, u, v = split(src)
# Descaling
descaled = core.descale.Debicubic(fvf.Depth(y, 32), get_w(855), 855, b, c)

# Fairly weak denoising. Stronger denoising on brighter areas of a frame.
# Done while descaled because it's overall faster *and* more effective.
d_mask = kgf.adaptive_grain(fvf.Depth(descaled, 16), show_mask=True, luma_scaling=6)
denoise_a = CoolDegrain(descaled, tr=1, thsad=72, thsadc=48, bits=16, blksize=8, overlap=4)
denoise_b = CoolDegrain(descaled, tr=1, thsad=24, thsadc=48, bits=16, blksize=8, overlap=4)
denoise = core.std.MaskedMerge(denoise_a, denoise_b, d_mask)

# Some AA to fix up instances of bad lineart.
# Done while descaled for similar reasons as L37
aa = lvf.upscaled_sraa(denoise)
aa = fvf.rfs(denoise, aa, mappings=f"[{edstart+890} {edstart+1032}]")

# Upscaling
upscaled = nnedi3_rpow2(aa).resize.Bicubic(src.width, src.height)
scaled = join([upscaled, u, v])


# Much like the denoising, way stronger debanding is performed on brighter areas.
# This way less perceivable detail is lost to the void. Darker areas will be grained stronger instead.
deb_d_mask = fvf.Depth(kgf.adaptive_grain(src, show_mask=True, luma_scaling=6), 16)
deband_a = core.f3kdb.Deband(scaled, range=21, y=56, cb=48, cr=48, grainy=12, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(scaled, range=16, y=40, cb=32, cr=32, grainy=24, grainc=0, output_depth=16)
deband = core.std.MaskedMerge(deband_a, deband_b, deb_d_mask)
deband = fvf.rfs(deband, deband_a, mappings=f"[{edstart+1494} {edstart+1600}]")

# Graining. Strong dynamic grain added to parts of the OP and darker slow-motion scenes.
grain = kgf.adaptive_grain(deband, 0.3, luma_scaling=6)


out = grain
final = fvf.Depth(out, 10)
final.set_output()
