import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import mvsfunc as mvf
import havsfunc as haf
from vsutil import *
core = vs.core

opstart, edstart = 1344, 31529


def _replace_credits(src_a, src_b, width, height, offset_x, offset_y, mappings):
    sqmask = kgf.squaremask(src_a, width, height, offset_x, offset_y)
    masked = core.std.MaskedMerge(src_a, src_b, sqmask)
    return fvf.rfs(src_a, masked, mappings)


def _create_credit_mask(src_descaled, src_upscaled, src_downscaled=None, binrz=0.05, max=6, infl=2):
    credit_mask = core.std.Expr([src_descaled, src_upscaled], 'x y - abs').std.Binarize(binrz)
    credit_mask = kgf.iterate(credit_mask, core.std.Maximum, max)
    credit_mask = kgf.iterate(credit_mask, core.std.Inflate, infl)
    return core.resize.Spline36(credit_mask, src_downscaled.width, src_downscaled.height) if src_downscaled else credit_mask


credits = [(1920, 60, 0, 733, f"[{opstart+37} {opstart+96}]"),
           (1920, 60, 0, 242, f"[{opstart+99} {opstart+160}]"),
           (1920, 60, 0, 445, f"[{opstart+171} {opstart+244}]"),
           (1056, 120, 152, 132, f"[{opstart+712} {opstart+783}]"),
           (940, 200, 850, 130, f"[{opstart+942} {opstart+1007}]"),
           (700, 70, 140, 130, f"[{opstart+1064} {opstart+1121}]"),
           (980, 325, 140, 660, f"[{opstart+1126} {opstart+1183}]"),
           (1920, 540, 0, 540, f"[{opstart+1322} {opstart+1460}]"),
           (820, 400, 1100, 0, f"[{opstart+1461} {opstart+1528}]"),
           (900, 400, 0, 0, f"[{opstart+1589} {opstart+1657}]"),
           (1920, 400, 0, 0, f"[{opstart+1760} {opstart+1873}]"),
           (900, 300, 510, 390, f"[{opstart+1898} {opstart+2156}]"),
           (1080, 800, 480, 135, f"[{edstart} {edstart+182}] [{edstart+207} {edstart+322}]"),
           (1100, 1080, 0, 0, f"[{edstart+421} {edstart+819}] [{edstart+949} {edstart+1049}] [{edstart+1923} {edstart+2011}]"),
           (1100, 1080, 820, 0, f"[{edstart+820} {edstart+915}] [{edstart+1054} {edstart+1175}] [{edstart+1645} {edstart+1739}]")]


src_a = lvf.src(r"BDMV/[BDMV]輪るピングドラム/[BDMV]輪るピングドラム 1/MAWARU PENGUINDRUM 1/BDMV/STREAM/00002.m2ts") # JP
src_b = lvf.src(r"BDMV/[BDMV] Mawaru Penguindrum (ITA)/MAWARU_PENGUINDRUM_01/BDMV/STREAM/00008.m2ts")     # ITA
src_b = src_b[23:]
scomp = lvf.scomp(src_a, src_b, height=360, make_diff=True) # tfw BDs dont match

l = core.std.CropRel(src_a, 0, 1918, 0, 0)
r = core.std.CropRel(src_a, 1918, 0, 0, 0)
m = core.std.CropRel(src_b, 2, 2, 0, 0)
src_b = core.std.StackHorizontal([l, m, r])

ya, ua, va = kgf.split(src_a)  # JP
yb, ub, vb = kgf.split(src_b)  # ITA

src = kgf.join([yb, ua, va])   # merge ITA luma with JP chroma
src = src[:-24]

for width, height, x, y, mappings in credits:
    src = _replace_credits(src, src_a, width, height, x, y, mappings)
src = fvf.rfs(src, src_a, mappings=f"[{edstart+1179} {edstart+1546}] [{edstart+2055} {edstart+2157}]") # Manual replacement

sqmask = kgf.squaremask(src, 849, 455, 0, 625)
masked = kgf.insert_clip(src, src[7032]*82, 7032)
src = core.std.MaskedMerge(src, masked, sqmask)
src = fvf.Depth(src, 32) # Mask fixes some twitching background lines


h = 720
b, c = 0, 1/2
thresh = .1
planes = split(src)
# Scaling. Clip is first descaled, then merged with a standard downscaled clip to deal with descaling errors.
descale = core.descale.Debicubic(planes[0], get_w(h), h, b, c)
downscale = core.resize.Spline36(planes[0], descale.width, descale.height)
upscaled = core.resize.Bicubic(descale, planes[0].width, planes[0].height, filter_param_a=b, filter_param_b=c)

credit_mask = _create_credit_mask(planes[0], upscaled, downscale)
lineart_mask = kgf.retinex_edgemask(haf.SMDegrain(fvf.Depth(descale, 16)))

planes[0] = core.std.Expr([descale, downscale], f'x {thresh} * y 1 {thresh} - * +')
planes[0] = core.std.MaskedMerge(descale, planes[0], fvf.Depth(lineart_mask, 32))
planes[0] = core.std.MaskedMerge(planes[0], downscale, credit_mask)

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
