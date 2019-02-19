import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import vsTAAmbk as taa
import havsfunc as haf
core = vs.core

# for splicing and audio
preview = 16662
endcard = 16782
part_b = 16902
epend = 19824

# so ED doesn't get killed by the filtering
edstart = 15584

src = lvf.src(r"05/[DragsterPS] Manariafurenzu Ekusutorapaato Zuke S01E05 [1080p] [Japanese Audio] [E78F90F0].mkv")
blank = core.std.BlankClip(src) # Part B starts too abruptly, so there's some space for a breather after ED.
src = src[:preview]+blank[:48]+src[part_b:]+src[preview:part_b]
src = fvf.Depth(src, 16)

scaled = core.resize.Spline36(src, 1440, 810)

denoise = lvf.denoise(scaled, h=0.4)
aa = taa.TAAmbk(denoise, aatype='Eedi3', opencl=True)

dbn = core.f3kdb.Deband(aa, range=18, y=48, cb=40, cr=40, grainy=0, grainc=0, output_depth=16)
grain = kgf.adaptive_grain(dbn, 0.4)

ed = scaled[edstart:preview]
insert = kgf.insert_clip(grain, ed, edstart)

out = insert
final = fvf.Depth(out, 10)
final.set_output()