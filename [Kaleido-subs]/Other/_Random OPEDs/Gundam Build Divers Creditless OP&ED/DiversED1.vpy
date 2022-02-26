import vapoursynth as vs
import fvsfunc as fvf
import kagefunc as kgf
core = vs.core

src = r"F:\Convert\[BDMV][180926][Gundam Build Divers][BD-BOX1]\GUNDAM_BUILD_DIVERS_BDBOX1_D3\BDMV\STREAM\00007.m2ts"
src = core.lsmas.LWLibavSource(src)
src = src[24:2184]
src = core.edgefixer.ContinuityFixer(src, left=[2,1,1],top=[2,1,1],bottom=[2,1,1], right=[2,1,1])
src = fvf.Depth(src, 16)

scaled = kgf.inverse_scale(src, height=720, kernel='spline36')

final = fvf.Depth(scaled, 10)
final.set_output()