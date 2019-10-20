import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
from nnedi3_rpow2 import *
from cooldegrain import *
from vsutil import *
from vsTAAmbk import *
core = vs.core

opstart, edstart = 1966, 32344

src = lvf.src(r'BDMV/[BDMV] Lord El-Melloi II-sei no Jikenbo ~Rail Zeppelin Grace Note~ [Vol.02]/BDROM/BDMV/STREAM/00000.m2ts')
src = src[24:-24]
ef = core.edgefixer.ContinuityFixer(src, 1, 1, 1, 1)
ef = fvf.Depth(ef, 32)


b, c = 0, 1/2
y, u, v = kgf.split(ef)
descaled = core.descale.Debicubic(y, 1280, 720, b, c)
upscaled = core.resize.Bicubic(descaled, y.width, y.height, filter_param_a=b, filter_param_b=c)
credit_mask = core.std.Expr([y, upscaled], 'x y - abs').std.Binarize(0.05)
credit_mask = kgf.iterate(credit_mask, core.std.Maximum, 6)
credit_mask = kgf.iterate(credit_mask, core.std.Inflate, 2)


d_mask = kgf.adaptive_grain(descaled, show_mask=True, luma_scaling=8)
denoise_a = CoolDegrain(descaled, tr=1, thsad=72, thsadc=48, bits=16, blksize=8, overlap=4)
denoise_b = CoolDegrain(descaled, tr=1, thsad=24, thsadc=48, bits=16, blksize=8, overlap=4)
denoise = core.std.MaskedMerge(denoise_a, denoise_b, fvf.Depth(d_mask, 16))

b_mask = fvf.Depth(core.std.Binarize(get_y(descaled), 0.45), 16).std.Invert()
l_mask = kgf.retinex_edgemask(fvf.Depth(descaled, 16))
l_mask = core.std.Expr([l_mask, b_mask], expr="x y -").std.Maximum().std.Inflate()
aa_a = lvf.transpose_aa(denoise)
aa_b = TAAmbk(denoise, aatype='Eedi3', mclip=l_mask, cycle=1)
motion_a = haf.QTGMC(aa_a, InputType=1, TR2=3)
motion_b = haf.QTGMC(aa_b, InputType=1, TR2=3)
aa_a = core.std.MaskedMerge(aa_a, motion_a, l_mask)
aa_b = core.std.MaskedMerge(aa_b, motion_b, l_mask)
aa = fvf.rfs(denoise, aa_a, mappings="[16987 17076] [17248 17345] [18328 18435]")
aa = fvf.rfs(aa, aa_b, mappings="[21056 21100]")
aa = fvf.Depth(aa, 32)

upscaled = nnedi3_rpow2(aa).resize.Bicubic(src.width, src.height)
upscaled = kgf.join([upscaled, u, v])
upscaled = core.std.MaskedMerge(upscaled, ef, credit_mask)
upscaled = fvf.Depth(upscaled, 16)


d_mask = fvf.Depth(kgf.adaptive_grain(ef, show_mask=True, luma_scaling=8), 16)
deband_a = core.f3kdb.Deband(upscaled, range=21, y=56, cb=48, cr=48, grainy=64, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(upscaled, range=16, y=40, cb=32, cr=32, grainy=64, grainc=0, output_depth=16)
deband = core.std.MaskedMerge(deband_a, deband_b, d_mask)

grain_a = kgf.adaptive_grain(deband, 0.15, luma_scaling=6)
grain_b = core.grain.Add(deband, var=3, uvar=0, constant=False)
grain = fvf.rfs(grain_a, grain_b, mappings=f"[{opstart+285} {opstart+573}]")


out = grain
final = fvf.Depth(out, 10)
final.set_output()
