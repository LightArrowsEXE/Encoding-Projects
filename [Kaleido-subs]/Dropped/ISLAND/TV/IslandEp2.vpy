import vapoursynth as vs
import mvsfunc as mvf
import vsTAAmbk as taa	
import kagefunc as kgf
import havsfunc as haf
import adjust
core = vs.core

opstart = 1056
edstart = 31768
opdenoisea = f'[{opstart+354} {opstart+482}]'
opdenoiseb = f'[{opstart+1624} {opstart+1647}]'
opnodark = f'[{opstart+1831} {opstart+1915}]'
opdebanda = f'[{opstart} {opstart+171}] [{opstart+1185} {opstart+1275}]'
opdebandb = f'[{opstart+483} {opstart+548}]'
opdebandc = f'[{opstart+901} {opstart+901}]'
opdebandd = f'[{opstart+902} {opstart+902}]'
opdebande = f'[{opstart+1624} {opstart+1647}]'
opdebandf = f'[{opstart+1648} {opstart+1732}]'
opdebandg = f'[{opstart+910} {opstart+1005}]'
dynamicgrain = f'[{opstart+1624} {opstart+1647}] [{edstart+1509} {edstart+1578}]'
ednodeband = f'[{edstart} {edstart+2157}]'

blackclipl = f'[{edstart-47} {edstart-1}]'

src = core.lsmas.LWLibavSource(r"F:\Portfolio\[Kaleido-subs]\ISLAND\src\EP2\ISLAND Episode 2 – I don't want you to feel bad-774619.mp4")
#Add dark clip for scenes that are supposed to be fully dark but for some reason aren't??
blackclip = core.std.BlankClip(src, length=150, color=[16, 128, 128])
src = core.remap.Rfs(src, blackclip, mappings=blackclipl)
src = core.resize.Spline36(src, 1280, 720, format=vs.YUV420P16)

srcY, srcU, srcV = kgf.split(src)
denoiseY = srcY.knlm.KNLMeansCL(3, 2, h=1.2)
denoiseY = mvf.BM3D(srcY, sigma=3, psample=1, radius1=1, ref=denoiseY)
denoiseY2 = srcY.dfttest.DFTTest(sigma=96, tbsize=1, sbsize=24, sosize=20)
denoiseY = core.remap.Rfs(srcY, denoiseY, mappings=opdenoisea)
denoiseY = core.remap.Rfs(denoiseY, denoiseY2, mappings=opdenoiseb)
denoised = kgf.join([denoiseY, srcU, srcV])

darken = haf.FastLineDarkenMOD(denoised, strength=36, protection=5, luma_cap=191, threshold=4, thinning=0)
darken = core.remap.Rfs(darken, denoised, mappings=opnodark)
aa = taa.TAAmbk(darken, aatype='Eedi3', opencl=True, cycle=0)

#deband1 is the generic deband, deband2 is heavy debanding for stuff like ep1's mid-episode fade
deband1 = core.f3kdb.Deband(aa, range=14, y=48, cb=40, cr=40, grainy=12, grainc=0, output_depth=16)
deband2 = core.f3kdb.Deband(aa, range=5, y=300, cb=280, cr=280, grainy=0, grainc=0, output_depth=16)
deband2 = core.f3kdb.Deband(deband2, range=21, y=72, cb=64, cr=64, grainy=64, grainc=0, output_depth=16)
deband = core.remap.Rfs(deband1, deband2, mappings="[14302 14421]")
#deband = deband1

OPdeband1 = core.f3kdb.Deband(aa, range=14, y=48, cb=40, cr=40, grainy=12, grainc=0, output_depth=16)
OPdeband2 = core.f3kdb.Deband(aa, range=16, y=56, cb=48, cr=48, grainy=0, grainc=0, output_depth=16)
OPdeband3 = core.f3kdb.Deband(aa, range=21, y=200, cb=180, cr=180, grainy=64, grainc=0, output_depth=16)
OPdeband4 = core.f3kdb.Deband(aa, range=24, y=500, cb=440, cr=440, grainy=64, grainc=0, output_depth=16)
OPdeband5 = core.f3kdb.Deband(aa, range=20, y=80, cb=72, cr=72, grainy=12, grainc=0, output_depth=16)
OPdeband5 = adjust.Tweak(OPdeband5, cont=0.8)
OPdeband6 = core.f3kdb.Deband(aa, range=17, y=56, cb=48, cr=48, grainy=36, grainc=0, output_depth=16)
OPdeband7 = core.f3kdb.Deband(aa, range=16, y=64, cb=56, cr=56, grainy=24, grainc=0, output_depth=16)
deband = core.remap.Rfs(aa, OPdeband1, mappings=opdebanda)
deband = core.remap.Rfs(deband, OPdeband2, mappings=opdebandb)
deband = core.remap.Rfs(deband, OPdeband3, mappings=opdebandc)
deband = core.remap.Rfs(deband, OPdeband4, mappings=opdebandd)
deband = core.remap.Rfs(deband, OPdeband5, mappings=opdebande)
deband = core.remap.Rfs(deband, OPdeband6, mappings=opdebandf)
deband = core.remap.Rfs(deband, OPdeband7, mappings=opdebandg)
deband = core.remap.Rfs(deband, aa, mappings=ednodeband)

mask = kgf.retinex_edgemask(denoised, sigma=1)
out = core.std.MaskedMerge(deband, aa, mask)

#grain2 is to be used in conjunction with deband2
grain1 = kgf.adaptive_grain(out, 0.2, luma_scaling=16)
grain2 = kgf.adaptive_grain(out, 2, luma_scaling=16, static=False)
grain = core.remap.Rfs(grain1, grain2, mappings="[14302 14421]")
#grain = grain1

dgrain = kgf.adaptive_grain(out, 1, luma_scaling=16, static=False)
out = core.remap.Rfs(grain, dgrain, mappings=dynamicgrain)

final = core.fmtc.bitdepth(out, bits=10, dmode=3)
final.set_output()