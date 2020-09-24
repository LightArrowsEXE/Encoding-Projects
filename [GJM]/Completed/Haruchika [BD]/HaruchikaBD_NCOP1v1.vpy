import kagefunc as kgf
import lvsfunc as lvf
import vapoursynth as vs
from awsmfunc import bbmod
from finedehalo import fine_dehalo
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


src = lvf.src(r"ハルチカ ~ハルタとチカは青春する~/HARUCHIKA_1/BDMV/STREAM/00010.m2ts")[24:-24]
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

detail_mask = lvf.denoise.detail_mask(aa, brz_a=0.08, brz_b=0.08)
deband = debander(aa, **deband_args)
deband = core.std.MaskedMerge(deband, aa, detail_mask)

grain = kgf.adaptive_grain(deband, 0.15, luma_scaling=4)


out = grain
final = depth(out, 10)
final.set_output()
