import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import mvsfunc as mvf
import havsfunc as haf
from vsutil import *
core = vs.core

opstart, edstart = 0, None


src_a = lvf.src(r"BDMV/[BDMV]輪るピングドラム/[BDMV]輪るピングドラム 2/MAWARU PENGUINDRUM 2/BDMV/STREAM/00010.m2ts") # JP
src_b = lvf.src(r"BDMV/[BDMV] Mawaru Penguindrum (ITA)/MAWARU_PENGUINDRUM_02/BDMV/STREAM/00015.m2ts")     # ITA
#src_b = src_b[23:]
scomp = lvf.scomp(src_a, src_b, height=480) # tfw BDs dont match

l = core.std.CropRel(src_a, 0, 1918, 0, 0)
r = core.std.CropRel(src_a, 1918, 0, 0, 0)
m = core.std.CropRel(src_b, 2, 2, 0, 0)
src_b = core.std.StackHorizontal([l, m, r])

ya, ua, va = kgf.split(src_a)  # JP
yb, ub, vb = kgf.split(src_b)  # ITA

src = kgf.join([yb, ua, va])   # merge ITA luma with JP chroma
src = src[24:-25]

src = fvf.Depth(src, 32)


h = 720
b, c = 0, 1/2
thresh = .1
planes = split(src)
# Scaling. Clip is first descaled, then merged with a standard downscaled clip to deal with descaling errors.
descale = core.descale.Debicubic(planes[0], get_w(h), h, b, c)
downscale = core.resize.Spline36(planes[0], descale.width, descale.height)

lineart_mask = kgf.retinex_edgemask(haf.SMDegrain(fvf.Depth(descale, 16)))

planes[0] = core.std.Expr([descale, downscale], f'x {thresh} * y 1 {thresh} - * +')
planes[0] = core.std.MaskedMerge(descale, planes[0], fvf.Depth(lineart_mask, 32))

planes[1], planes[2] = [core.resize.Bicubic(p, planes[0].width, planes[0].height, src_left=.25) for p in planes[1:]]

scaled = join(planes)
descaled = join([descale, planes[1], planes[2]]) # for comparison


# Filterchain
denoise = mvf.BM3D(scaled, sigma=[0.5,1.5], depth=16, profile1='high')

d_mask = kgf.adaptive_grain(fvf.Depth(scaled, 16), show_mask=True, luma_scaling=8)
deband_a = core.f3kdb.Deband(denoise, range=18, y=32, cb=48, cr=48, grainy=24, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(denoise, range=16, y=48, cb=48, cr=48, grainy=48, grainc=0, output_depth=16)
deband = core.std.MaskedMerge(deband_a, deband_b, d_mask)
grain = kgf.adaptive_grain(deband, 0.1, luma_scaling=8)


out = grain
final = fvf.Depth(out, 10)
final.set_output()
