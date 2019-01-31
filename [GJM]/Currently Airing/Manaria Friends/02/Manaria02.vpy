import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import vsTAAmbk as taa
import havsfunc as haf
core = vs.core

preview = 16662
part_b = 16902
edstart = 15584
endcard = 16782
src = src[24:preview]+blank[0:48]+src[part_b:]+src[preview:part_b]
src = lvf.src(r"[DragsterPS] Manariafurenzu Ekusutorapaato Zuke S01E02 [1080p] [Japanese Audio] [7A8A7C74].mkv")
blank = core.std.BlankClip(src)
src = src[24:preview]+blank[:48]+src[part_b:]+src[preview:part_b]
src = fvf.Depth(src, 16)

scaled = core.resize.Spline36(src, 1440, 810)

denoise = lvf.denoise(scaled, h=0.4)
aa = taa.TAAmbk(denoise, aatype='Eedi3', opencl=True)

dbn_a = core.f3kdb.Deband(aa, range=18, y=48, cb=40, cr=40, grainy=0, grainc=0, output_depth=16)
dbn_b = core.f3kdb.Deband(aa, range=5, y=200, cb=200, cr=200, grainy=0, grainc=0, output_depth=16)
dbn_b = core.f3kdb.Deband(dbn_b, range=21, y=80, cb=72, cr=72, grainy=24, grainc=0, output_depth=16)
dbn = fvf.rfs(dbn_a, dbn_b, mappings="[6458 6527]")

grain_a = kgf.adaptive_grain(dbn, 0.4)
grain_b = core.grain.Add(dbn, var=0.7, uvar=0, constant=False)
grain_c = kgf.adaptive_grain(dbn, 1)
grain = fvf.rfs(grain_a, grain_b, mappings="[6477 6527]")
grain = fvf.rfs(grain, grain_c, mappings="[1234 1357] [9204 9501]")

ed = scaled[edstart:preview]
insert = kgf.insert_clip(grain, ed, edstart)

out = insert
final = fvf.Depth(out, 10)
final.set_output()