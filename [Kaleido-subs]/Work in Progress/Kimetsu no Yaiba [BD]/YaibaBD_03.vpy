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

opstart, edstart = 2972-2159, 33085-2159
b, c = 1/5, 2/5

darker_shots = """
               """

src = lvf.src(r"BDMV/[BDMV][190828][Kimetsu no Yaiba][Vol.2]/BDMV/STREAM/00004.m2ts")
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

denoise_a = mvf.BM3D(w2x, sigma=1)
denoise_b = mvf.BM3D(w2x, sigma=3)
denoise = fvf.rfs(denoise_a, denoise_b, mappings=darker_shots)
denoise = fvf.Depth(denoise, 16)

aa_a = TAAmbk(denoise, aatype='Eedi3')
aa_b = TAAmbk(denoise, aatype='Nnedi3SangNom', cycle=2, repair=2)
aa_c = knnAA(denoise)
aa = fvf.rfs(denoise, aa_a, mappings=f"""[{opstart+284} {opstart+406}] [{opstart+1017} {opstart+1079}] [{opstart+1312} {opstart+1368}] {opstart+1593} {opstart+1594} [{opstart+1895} {opstart+2003}] 
                                         [{edstart+890} {edstart+1032}]""")
aa = fvf.rfs(aa, aa_b, mappings="")
aa = fvf.rfs(aa, aa_c, mappings="")

upscaled = nnedi3_rpow2(aa).resize.Bicubic(src.width, src.height)
upscaled = kgf.join([upscaled, u, v])
m_upscaled = core.std.MaskedMerge(upscaled, src, fvf.Depth(credit_mask, 16))
scaled = fvf.rfs(upscaled, m_upscaled, mappings=f"""[{opstart} {opstart+2159}] 
                                                    [{edstart} {edstart+2159}]""")


deband_a = core.f3kdb.Deband(scaled, range=16, y=32, cb=40, cr=40, grainy=24, grainc=0, output_depth=16, sample_mode=1)
deband_b = core.f3kdb.Deband(scaled, range=18, y=40, cb=48, cr=48, grainy=36, grainc=0, output_depth=16, sample_mode=1)
deband_c = core.f3kdb.Deband(scaled, range=21, y=48, cb=48, cr=48, grainy=36, grainc=0, output_depth=16, sample_mode=1)
deband = fvf.rfs(deband_a, deband_b, mappings=f"""[{opstart+742} {opstart+784}] [{opstart+1128} {opstart+1287}] [{opstart+1592} {opstart+1616}] [{opstart+2004} {opstart+2046}] 
                                                  [{edstart+1494} {edstart+1600}] 
                                                  [3537 3584] [13298 13393]""")
deband = fvf.rfs(deband, deband_c, mappings=darker_shots + "")

grain_a = kgf.adaptive_grain(deband, 0.3, luma_scaling=4)
grain_b = kgf.adaptive_grain(deband, 1)
grain_c = core.grain.Add(deband, 10, constant=False)
grain_d = kgf.adaptive_grain(deband, 2.5, static=False, luma_scaling=24)
grain = fvf.rfs(grain_a, grain_b, mappings=f"""[{opstart+1128} {opstart+1296}] 
                                               [8208 8358]""")
grain = fvf.rfs(grain, grain_c, mappings=f"[{opstart+28} {opstart+288}] [{opstart+401} {opstart+406}] [{opstart+1313} {opstart+1368}]")
grain = fvf.rfs(grain, grain_d, mappings=darker_shots)


out = grain
final = fvf.Depth(out, 10)
final.set_output()
