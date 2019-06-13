import vapoursynth as vs
import fvsfunc as fvf
import kagefunc as kgf
import mvsfunc as mvf
import havsfunc as haf
core = vs.get_core()

src = r"F:\Portfolio\[Kaleido-subs]\Last Period (RAW)\src\[BDMV][180727][ラストピリオド -終わりなき螺旋の物語][Vol.2]\LAST_PERIOD_2\BDMV\STREAM\00008.m2ts"
src = core.lsmas.LWLibavSource(src)
src = src[0:2160]
src = fvf.Depth(src, 16)
srcY, srcU, srcV = kgf.split(src)

denoiseY = srcY.knlm.KNLMeansCL(3, 2, h=0.4)
denoiseY = mvf.BM3D(srcY, sigma=3, psample=0, radius1=1, ref=denoiseY)
denoised = kgf.join([denoiseY, srcU, srcV])

sharpen = haf.ContraSharpening(denoised, src, radius=None, rep=13, planes=[0])

deband = core.f3kdb.Deband(sharpen, range=16, y=40, cb=32, cr=32, grainy=0, grainc=0, output_depth=16)

out = deband
final = fvf.Depth(out, 10)
final.set_output()
