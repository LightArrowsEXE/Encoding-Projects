import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import vsTAAmbk as taa
import havsfunc as haf
core = vs.core

edstart = 15586

src = lvf.src(r"../01/[HorribleSubs] Manaria Friends - 01 [1080p].mkv")
src = src[24:20217]
src = fvf.Depth(src, 16)

scaled = core.resize.Spline36(src, 1440, 810)

denoise = lvf.denoise(scaled, h=1.8)
aa = taa.TAAmbk(denoise, aatype='Eedi3')
dbn = core.f3kdb.Deband(aa, range=23, y=64, cb=56, cr=56, grainy=24, grainc=0, output_depth=16)

grain = kgf.adaptive_grain(dbn, 1.5)

ed = scaled[edstart:edstart+1199]
insert = kgf.insert_clip(grain, ed, edstart)

rfs = fvf.rfs(insert, scaled, mappings="[19798 20192]")

out = rfs
final = fvf.Depth(out, 10)
final.set_output()