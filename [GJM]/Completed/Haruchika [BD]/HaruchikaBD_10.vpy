import kagefunc as kgf
import lvsfunc as lvf
import vapoursynth as vs
from awsmfunc import bbmod
from finedehalo import fine_dehalo
from vardefunc import diff_creditless_mask as DCM
from vsutil import depth, get_w, get_y, join, plane, split

core = vs.core


def reconstruct(clip: vs.VideoNode) -> vs.VideoNode:
    # Reconstruct the chroma to fix how ugly it looks
    def _rescale(clip: vs.VideoNode) -> vs.VideoNode:
        return core.resize.Bicubic(clip, width=1920, height=1080)
    planes = split(clip)
    planes[0] = core.resize.Point(planes[0], planes[1].width, planes[1].height)
    planes = map(_rescale, (planes))
    return join([*planes])


def demangle(clip: vs.VideoNode) -> vs.VideoNode:
    return core.resize.Bicubic(clip, 1920, 1080, src_left=0.5)


def create_mask(clip: vs.VideoNode, height: vs.VideoNode) -> vs.VideoNode:
    downscale = clip.resize.Bicubic(clip.width/2, clip.height/2)
    mask = fine_dehalo(downscale, showmask=1)
    return mask.resize.Bicubic(get_w(height), height)


def debander(clip: vs.VideoNode, **deband_args) -> vs.VideoNode:
    return join([
        core.placebo.Deband(plane(clip, 0), grain=6, **deband_args),
        core.placebo.Deband(plane(clip, 1), grain=0, **deband_args),
        core.placebo.Deband(plane(clip, 2), grain=0, **deband_args)
    ])

# Common args
scale_args = dict(kernel=lvf.kernels.Bicubic(b=0, c=1/2))
deband_args = dict(iterations=2, threshold=4, radius=14)

# first frame of OP, first frame of ED, first frame of extra
# Note to self: Double-check OP version every episode, ED can only work for second-to-last episode
opstart = 1320
edstart = None
extra = None

src = lvf.src(r"ハルチカ ~ハルタとチカは青春する~/HARUCHIKA_5/BDMV/STREAM/00004.m2ts")[24:-24]


if opstart is not None: # Check trims every episode
    src_NCOP = lvf.src(r'ハルチカ ~ハルタとチカは青春する~/HARUCHIKA_4/BDMV/STREAM/00011.m2ts')[24:-26]
    scomp_op = lvf.scomp(src[opstart:opstart+src_NCOP.num_frames], src_NCOP, make_diff=True)
if edstart is not None:
    src_NCED = lvf.src(r'ハルチカ ~ハルタとチカは青春する~/HARUCHIKA_3/BDMV/STREAM/00010.m2ts')[24:-24]
if extra is not None:
    src_extra = lvf.src(r'ハルチカ ~ハルタとチカは青春する~/HARUCHIKA_1/BDMV/STREAM/00011.m2ts')[24:2099]
    scomp = lvf.scomp(src[extra:extra+src_extra.num_frames], src_extra, make_diff=True)


# Mask for OP/ED/Extra credits
op_mask = DCM(src, src[opstart:opstart+src_NCOP.num_frames], src_NCOP, opstart, opstart+src_NCOP.num_frames) \
    if opstart is not None else core.std.BlankClip(src)
ed_mask = DCM(src, src[edstart:edstart+src_NCED.num_frames], src_NCED, opstart, opstart+src_NCED.num_frames) \
    if edstart is not None else core.std.BlankClip(src)
extra_mask = DCM(src, src[extra:extra+src_extra.num_frames], src_extra, extra, extra+src_extra.num_frames) \
    if extra is not None else core.std.BlankClip(src)


credit_mask = core.std.Expr([get_y(op_mask), get_y(ed_mask), get_y(extra_mask)], expr='x y + z +') \
    .resize.Bicubic(get_w(720), 720)
credit_mask = depth(credit_mask, 32)

ef = bbmod(src, left=2, right=2, top=2, bottom=2,
           thresh=100, blur=999, scale_thresh=False,
           y=True, u=False, v=False)
ef = depth(ef, 32)


downscaled = core.resize.Bicubic(ef, get_w(720), 720, format=vs.YUV444PS)
descaled = core.std.MaskedMerge(
    get_y(downscaled), lvf.scale.descale(ef, upscaler=None, **scale_args),
    lvf.util.quick_resample(downscaled, kgf.retinex_edgemask).std.Deflate())
descaled = core.std.MaskedMerge(
    descaled, get_y(downscaled), depth(create_mask(ef, downscaled.height), 32))
recon = demangle(reconstruct(ef)).resize.Bicubic(descaled.width, descaled.height)
scaled = join([descaled, plane(recon, 1), plane(recon, 2)])


aa = lvf.aa.nneedi3_clamp(scaled, strength=1.5)

merged = core.std.MaskedMerge(aa, downscaled, credit_mask)

detail_mask = lvf.denoise.detail_mask(merged, brz_a=0.08, brz_b=0.08)
deband = debander(merged, **deband_args)
deband = core.std.MaskedMerge(deband, merged, detail_mask)

grain = kgf.adaptive_grain(deband, 0.15, luma_scaling=4)


out = grain
final = depth(out, 10)
final.set_output()
