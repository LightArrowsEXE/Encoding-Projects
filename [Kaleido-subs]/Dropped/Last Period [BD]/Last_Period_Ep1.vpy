import vapoursynth as vs
import fvsfunc as fvf
import kagefunc as kgf
import mvsfunc as mvf
import havsfunc as haf
import lvsfunc as lvf
core = vs.core

opstart = 1630
edstart = 31768
ed_banding = f'[{edstart} {edstart+13}] [{edstart+46} {edstart+49}] [{edstart+83} {edstart+86}] [{edstart+197} {edstart+424}] [{edstart+624} {edstart+629}] [{edstart+643} {edstart+770}] [{edstart+891} {edstart+1001}] [{edstart+1166} {edstart+1393}] [{edstart+1464} {edstart+1693}] [{edstart+1764} {edstart+1919}]'
banding = "[26938 27162] [28623 29617] [29624 30101] [30320 30777]"
awful_banding = "[1566 1629] [11982 12004] [26684 26854] [29618 29623] [30168 30319] [30778 30960] [31673 31767]"

src = r"F:\Portfolio\[Kaleido-subs]\Last Period (RAW)\src\[BDMV][180627][ラストピリオド -終わりなき螺旋の物語][Vol.1]\LAST_PERIOD_1\BDMV\STREAM\00004.m2ts"
src = core.lsmas.LWLibavSource(src)
src = src[0:34046]
src = fvf.Depth(src, 16)
srcY, srcU, srcV = kgf.split(src)

denoiseY = srcY.knlm.KNLMeansCL(3, 2, h=0.8)
denoiseY = mvf.BM3D(srcY, sigma=3, psample=0, radius1=1, ref=denoiseY)
denoised = kgf.join([denoiseY, srcU, srcV])

sharpen = haf.ContraSharpening(denoised, src, planes=[0])
sharpen = core.remap.Rfs(denoised, sharpen, mappings=f'[{opstart} {opstart+2159}] [{edstart} {edstart+2159}]')

aa = lvf.fix_eedi3(sharpen)

deband_a = core.f3kdb.Deband(aa, range=16, y=56, cb=48, cr=48, grainy=0, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(aa, range=18, y=64, cb=56, cr=56, grainy=12, grainc=0, output_depth=16)
deband_c = core.f3kdb.Deband(aa, range=21, y=80, cb=72, cr=72, grainy=12, grainc=0, output_depth=16)
deband = core.remap.Rfs(deband_a, deband_b, mappings=f'{ed_banding} {banding}')
deband = core.remap.Rfs(deband, deband_b, mappings=awful_banding)

grain = kgf.adaptive_grain(deband, 1, static=False)
grain = core.remap.Rfs(deband, grain, mappings=awful_banding)

out = grain
final = fvf.Depth(out, 10)
final.set_output()
