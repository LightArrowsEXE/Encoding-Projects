import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import vsTAAmbk as taa
import havsfunc as haf
core = vs.core

preview = 16688
part_b = 16928
edstart = 15586

src_a = lvf.src(r"..\01\Mysteria Friends E01 [1080p][E-AC3][JapDub][GerSub][Web-DL].mkv")
src_b = lvf.src(r"..\01\Mysteria Friends E01v2 [1080p][E-AC3][JapDub][GerSub][Web-DL].mkv")
blank = core.std.BlankClip(src_a)
src = src_a[24:preview]+blank[:48]+src_b[part_b:]+src_a[preview:part_b]
src = fvf.Depth(src, 16)

scaled = core.resize.Spline36(src, 1440, 810)

denoise = lvf.denoise(scaled, h=0.4)
aa = taa.TAAmbk(denoise, aatype='Eedi3')
dbn = core.f3kdb.Deband(aa, range=17, y=40, cb=32, cr=32, grainy=0, grainc=0, output_depth=16)

grain = kgf.adaptive_grain(dbn, 0.4)

ed = scaled[edstart:preview]
insert = kgf.insert_clip(grain, ed, edstart)

out = insert
final = fvf.Depth(out, 10)
final.set_output()