import vapoursynth as vs
import fvsfunc as fvf
import kagefunc as kgf
import mvsfunc as mvf
import havsfunc as haf
core = vs.get_core()

edstart = 0
ed_banding = f'[{edstart} {edstart+13}] [{edstart+46} {edstart+49}] [{edstart+83} {edstart+86}] [{edstart+197} {edstart+424}] [{edstart+624} {edstart+629}] [{edstart+643} {edstart+770}] [{edstart+891} {edstart+1001}] [{edstart+1166} {edstart+1393}] [{edstart+1464} {edstart+1693}] [{edstart+1764} {edstart+1919}]'

src = r"F:\Portfolio\[Kaleido-subs]\Last Period (RAW)\src\[BDMV][180727][ラストピリオド -終わりなき螺旋の物語][Vol.2]\LAST_PERIOD_2\BDMV\STREAM\00009.m2ts"
src = core.lsmas.LWLibavSource(src)
src = src[0:2160]
src = fvf.Depth(src, 16)
srcY, srcU, srcV = kgf.split(src)

denoiseY = srcY.knlm.KNLMeansCL(3, 2, h=0.8)
denoiseY = mvf.BM3D(srcY, sigma=3, psample=0, radius1=1, ref=denoiseY)
denoised = kgf.join([denoiseY, srcU, srcV])

sharpen = haf.ContraSharpening(denoised, src, radius=None, rep=13, planes=[0])

deband_a = core.f3kdb.Deband(sharpen, range=16, y=56, cb=48, cr=48, grainy=0, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(sharpen, range=18, y=64, cb=56, cr=56, grainy=12, grainc=0, output_depth=16)
deband = core.remap.Rfs(deband_a, deband_b, mappings=ed_banding)

out = deband
final = fvf.Depth(out, 10)
final.set_output()
