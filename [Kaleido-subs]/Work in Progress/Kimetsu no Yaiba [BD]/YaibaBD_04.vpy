import vapoursynth as vs
import fvsfunc as fvf
import kagefunc as kgf
import lvsfunc as lvf
import mvsfunc as mvf
from vsTAAmbk import TAAmbk
from nnedi3_rpow2 import nnedi3_rpow2
from vsutil import get_w
from knnfunc import knnAA
core = vs.core

opstart, edstart = 3572-2159, 33085-2159
b, c = 1/5, 2/5

darker_shots = """
               [3795 4588]
               [16325 16360]
               [16457 16499]
               [24252 24695]
               [24986 25201]
               [30630 30662]
               """

src = lvf.src(r"BDMV/[BDMV][190828][Kimetsu no Yaiba][Vol.2]/BDMV/STREAM/00005.m2ts")
src = src[:34046]
src = fvf.Depth(src, 16)


y, u, v = kgf.split(src)
descaled = core.descale.Debicubic(fvf.Depth(y, 32), get_w(855), 855, b, c)
upscaled = core.resize.Bicubic(descaled, y.width, y.height, filter_param_a=b, filter_param_b=c)
credit_mask = core.std.Expr([fvf.Depth(y, 32), upscaled], 'x y - abs').std.Binarize(0.05)
credit_mask = kgf.iterate(credit_mask, core.std.Maximum, 6)
credit_mask = kgf.iterate(credit_mask, core.std.Inflate, 2)

w2x = core.resize.Point(mvf.ToYUV(core.w2xc.Waifu2x(mvf.ToRGB(descaled), noise=1, scale=1, gpu=0)), format=descaled.format)
w2x = fvf.rfs(descaled, w2x, mappings=f"{opstart+1593} {opstart+1594}")

denoise_a = mvf.BM3D(w2x, sigma=1.25)
denoise_b = mvf.BM3D(w2x, sigma=3)
denoise = fvf.rfs(denoise_a, denoise_b, mappings=darker_shots + "[25865 25892] [30585 30629]")
denoise = fvf.Depth(denoise, 16)

aa_a = TAAmbk(denoise, aatype='Eedi3')
aa_b = TAAmbk(denoise, aatype='Nnedi3SangNom', cycle=2, repair=2)
aa_c = knnAA(denoise)
aa = fvf.rfs(denoise, aa_a, mappings=f"""[{opstart+284} {opstart+406}] [{opstart+1017} {opstart+1079}] [{opstart+1312} {opstart+1368}] {opstart+1593} {opstart+1594} [{opstart+1895} {opstart+2003}]
                                         [{edstart+890} {edstart+1032}]
                                         [16433 16456] [22999 23162]""")
aa = fvf.rfs(aa, aa_b, mappings=f"[{edstart+2160} {edstart+2175}]")
aa = fvf.rfs(aa, aa_c, mappings=darker_shots + "[16361 16432]")

upscaled = nnedi3_rpow2(aa).resize.Bicubic(src.width, src.height)
upscaled = kgf.join([upscaled, u, v])
m_upscaled = core.std.MaskedMerge(upscaled, src, fvf.Depth(credit_mask, 16))
scaled = fvf.rfs(upscaled, m_upscaled, mappings=f"""[{opstart} {opstart+2159}]
                                                    [{edstart} {edstart+2159}]""")


deband_a = core.f3kdb.Deband(scaled, range=17, y=32, cb=32, cr=32, grainy=24, grainc=0, output_depth=16, sample_mode=1)
deband_b = core.f3kdb.Deband(scaled, range=19, y=48, cb=48, cr=48, grainy=36, grainc=0, output_depth=16, sample_mode=1)
deband_c = core.f3kdb.Deband(scaled, range=21, y=48, cb=48, cr=48, grainy=36, grainc=0, output_depth=16, sample_mode=1)
deband_d = core.f3kdb.Deband(scaled, range=5, y=48, cb=48, cr=48, grainy=0, grainc=0, output_depth=16, sample_mode=1)
deband_d = core.f3kdb.Deband(deband_d, range=16, y=48, cb=48, cr=48, grainy=24, grainc=0, output_depth=16, sample_mode=1)
deband = fvf.rfs(deband_a, deband_b, mappings=f"""[{opstart+742} {opstart+784}] [{opstart+1128} {opstart+1287}] [{opstart+1592} {opstart+1616}] [{opstart+2004} {opstart+2046}]
                                                  [{edstart+1494} {edstart+1600}]""")
deband = fvf.rfs(deband, deband_c, mappings=darker_shots + "[22999 23162]")
deband = fvf.rfs(deband, deband_d, mappings="[25865 25892]")

grain_a = kgf.adaptive_grain(deband, 0.3, luma_scaling=4)
grain_b = kgf.adaptive_grain(deband, 1)
grain_c = core.grain.Add(deband, 10, constant=False)
grain_d = core.grain.Add(deband, var=4, uvar=0, constant=False)
grain = fvf.rfs(grain_a, grain_b, mappings=f"""[{opstart+1128} {opstart+1296}]
                                               [22999 23162] [25865 25892]""")
grain = fvf.rfs(grain, grain_c, mappings=f"[{opstart+28} {opstart+288}] [{opstart+401} {opstart+406}] [{opstart+1313} {opstart+1368}]")
grain = fvf.rfs(grain, grain_d, mappings=darker_shots)


out = grain
final = fvf.Depth(out, 10)
final.set_output()
