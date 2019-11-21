import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import havsfunc as haf
from vsutil import *
from cooldegrain import *
from vsTAAmbk import *
core = vs.core

opstart, edstart = None, None

src = lvf.src(r'BDMV/Vol 1/BDROM/BDMV/STREAM/00000.m2ts')
src = src[24:-24]
ef = core.edgefixer.ContinuityFixer(src, 1, 1, 1, 1)
ef = fvf.Depth(ef, 32)


descaled = kgf.inverse_scale(ef, height=720,
                           kernel='bicubic', b=0, c=1/2,
                           mask_detail=True)

d_mask = kgf.adaptive_grain(descaled, show_mask=True, luma_scaling=8)
denoise_a = CoolDegrain(descaled, tr=1, thsad=72, thsadc=48, bits=16, blksize=8, overlap=4)
denoise_b = CoolDegrain(descaled, tr=1, thsad=24, thsadc=48, bits=16, blksize=8, overlap=4)
denoise = core.std.MaskedMerge(denoise_a, denoise_b, fvf.Depth(d_mask, 16))

b_mask = fvf.Depth(core.std.Binarize(get_y(descaled), 0.30), 16).std.Invert()
l_mask_a = kgf.retinex_edgemask(denoise).std.Maximum()
l_mask_b = kgf.retinex_edgemask(fvf.Depth(descaled, 16))
l_mask_b = core.std.Expr([l_mask_b, b_mask], expr="x y -").std.Maximum().std.Inflate()
aa_a = lvf.nneedi3_clamp(denoise, mask=l_mask_a, strength=1.7)
aa_b = TAAmbk(denoise, aatype='Eedi3', mclip=l_mask_b, cycle=1)
motion = haf.QTGMC(aa_b, InputType=1, TR2=3)
aa_b = core.std.MaskedMerge(aa_b, motion, l_mask_b)
aa = fvf.rfs(aa_a, aa_b, mappings="[22787 22902]")


d_mask = fvf.Depth(kgf.adaptive_grain(descaled, show_mask=True, luma_scaling=8), 16)
deband_a = core.f3kdb.Deband(aa, range=19, y=56, cb=48, cr=48, grainy=64, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(aa, range=16, y=40, cb=32, cr=32, grainy=64, grainc=0, output_depth=16)
deband = core.std.MaskedMerge(deband_a, deband_b, d_mask)

grain = kgf.adaptive_grain(deband, 0.15, luma_scaling=6)


out = grain
final = fvf.Depth(out, 10)
final.set_output()
