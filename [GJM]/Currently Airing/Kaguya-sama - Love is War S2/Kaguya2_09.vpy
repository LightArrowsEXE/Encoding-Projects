from functools import partial
import os

import havsfunc as haf
import kagefunc as kgf
import lvsfunc as lvf
import mvsfunc as mvf
from descale import Debicubic
from nnedi3_resample import nnedi3_resample
from toolz import functoolz
from vsutil import depth, get_w, get_y, iterate, join, plane, split

import vapoursynth as vs

core = vs.core

shader = 'FSRCNNX_x2_56-16-4-1.glsl'
if os.path.exists(shader) is False:
    hookpath = "mpv/shaders/mpv/shaders/FSRCNNX_x2_56-16-4-1.glsl"
    shader = os.path.join(os.getenv("APPDATA"), hookpath)


def fsrcnnx_reupscale(clip: vs.VideoNode, ref: vs.VideoNode,
                      width: int = 1920, height: int = 1080) -> vs.VideoNode:
    descaled = clip.resize.Point(format=vs.YUV444P16)
    descaled = depth(
        core.placebo.Shader(descaled, width=src.width * 2, height=src.height * 2,
                            shader=shader, filter='mitchell'),
                     32)
    descaled = core.resize.Bicubic(descaled, width, height)
    return join([get_y(descaled), plane(ref, 1), plane(ref, 2)])


@functoolz.curry
def denoise(clip: vs.VideoNode) -> vs.VideoNode:
    detail_mask = _generate_detail_mask(clip)
    denoise = mvf.BM3D(clip, sigma=[1.5, 0], profile1='lc')
    denoise = core.std.MaskedMerge(denoise, clip, detail_mask)
    return mvf.BM3D(clip, sigma=[0, 2], profile1='lc')


@functoolz.curry
def fix_lineart(clip: vs.VideoNode) -> vs.VideoNode:
    dehalo = lvf.util.quick_resample(
        clip, partial(haf.FineDehalo, rx=2.4, darkstr=0, brightstr=1, contra=1))
    return lvf.util.quick_resample(
        dehalo, partial(haf.EdgeCleaner, strength=4, rmode=13, smode=1, hot=True))


@functoolz.curry
def merge_credits(clip: vs.VideoNode, og_clip: vs.VideoNode,
                  h: int, b: float, c: float) -> vs.VideoNode:
    credit_mask = _create_credit_mask(og_clip, h, b, c, brz=0.1)
    return core.std.MaskedMerge(clip, og_clip, credit_mask)


@functoolz.curry
def deband(clip: vs.VideoNode, og_clip: vs.VideoNode) -> vs.VideoNode:
    detail_mask = _generate_detail_mask(og_clip)
    deband = core.placebo.Deband(clip, planes=1, iterations=1, threshold=2, radius=12, grain=4)
    deband = core.std.MaskedMerge(deband, og_clip, detail_mask)
    deband = core.placebo.Deband(deband, planes=2|4, iterations=3, threshold=4, radius=20, grain=0)
    return kgf.adaptive_grain(deband, 0.35, luma_scaling=4)


def dehardsub(clip_a: vs.VideoNode, clip_b: vs.VideoNode) -> vs.VideoNode:
    hardsubmask = kgf.hardsubmask(clip_a, clip_b)
    clip = core.std.MaskedMerge(clip_a, clip_b, hardsubmask)

    hardsubmask_fade = lvf.util.quick_resample(
        clip_a, partial(kgf.hardsubmask_fades, ref=clip_b, expand_n=15, highpass=600)
    )
    clip_fade = core.std.MaskedMerge(clip_a, clip_b, hardsubmask_fade)
    clip = lvf.rfs(clip, clip_fade, ranges=op_signs + hs_signs)
    if replace_scenes:
        clip = lvf.rfs(clip, clip_b, ranges=replace_scenes)
    return clip


def rescale_blur(clip: vs.VideoNode,
                 h: int, b: float, c: float
                 ) -> vs.VideoNode:
    planes = split(clip)
    descaled = Debicubic(planes[0], get_w(h), h, b=b, c=c)

    pre_den = core.knlm.KNLMeansCL(descaled, d=2, a=3, h=1.2, device_type='gpu')
    l_mask = core.std.Prewitt(pre_den, scale=5)
    l_mask = iterate(l_mask, core.std.Deflate, 6).std.Binarize(0.08)

    blur = lvf.util.quick_resample(descaled, partial(core.bilateral.Bilateral, sigmaS=4.5, sigmaR=0.01))
    blur = core.std.MaskedMerge(descaled, blur, l_mask)
    blur = lvf.rfs(descaled, blur, ranges=op_range)

    interp = lvf.util.quick_resample(blur, partial(haf.QTGMC, InputType=1, TR2=3))
    interp = lvf.rfs(blur, interp, ranges=op_interp)

    return fsrcnnx_reupscale(interp, clip)


def _create_credit_mask(clip: vs.VideoNode,
                        h: int, b: float, c: float,
                        brz: float = 0.05
                        ) -> vs.VideoNode:
    clip_y = get_y(clip)
    descaled = Debicubic(clip_y, get_w(h), h, b=b, c=c)
    upscaled = core.resize.Bicubic(descaled, clip_y.width, clip_y.height, filter_param_a=b, filter_param_b=c)
    credit_mask = core.std.Expr([clip_y, upscaled], 'x y - abs').std.Binarize(brz)
    credit_mask = iterate(credit_mask, core.std.Maximum, 4)
    return iterate(credit_mask, core.std.Inflate, 2)


def _generate_detail_mask(clip: vs.VideoNode) -> vs.VideoNode:
    return lvf.denoise.detail_mask(clip, pre_denoise=3.6, brz_a=0.025, brz_b=0.005)


upscaled_args = dict(width=1552, height=873, kernel=lvf.kernels.Bicubic(1/3, 1/3))


opstart = 408

op_signs = [(opstart+397, opstart+508)] \
    if opstart is not None else []
op_range = [(opstart, opstart+2157)] \
    if opstart is not None else []
op_interp = [(opstart+594, opstart+628)] \
    if opstart is not None else []

hs_signs = [
    (127, 200), (2566, 2835), (3290, 3376), (7027, 7087),
    (8126, 8158), (10884, 10893), (10961, 10965), (10976, 10979),
    (11004, 11008), (11018, 11021), (12833, 12909), 13790,
    (13943, 14001), (14050, 14173), (16109, 16159), (19391, 19437),
    (19453, 19521), (19578, 20037), (20490, 20493), (21085, 21133),
    (21164, 21505), (21793, 21797), (21852, 21858), (22394, 22480),
    (23654, 23753), (24881, 24964), (26247, 26348), (31033, 31074),
    (31402, 31443), (31756, 31833), (34368, 34371), (34444, 34451)
]

replace_scenes = [

]


src_wk = lvf.misc.source(r"09/Kaguya-Sama Love is War S02E09 [1080p][AAC][JapDub][GerSub][Web-DL].mkv")
src_fu = lvf.misc.source(r"09/[HorribleSubs] Kaguya-sama wa Kokurasetai S2 - 09 [1080p].mkv")[289:]
src_wk = src_wk[4:22273] + src_wk[22272] * 5 + src_wk[22273:]
scomp = lvf.comparison.stack_compare(src_wk, src_fu, make_diff=True, warn=True)

src = dehardsub(src_wk, src_fu)
scomp2 = lvf.comparison.stack_compare(src, src_fu, make_diff=True)

# diff = lvf.comparison.tvbd_diff(src, src_fu, thr=104)
src = depth(src, 32)


h = 874
b, c = 0, 1/2
scaled = rescale_blur(src, h=h, b=b, c=c)


filter_chain = functoolz.compose(
    denoise,
    fix_lineart,
    merge_credits(og_clip=src, h=h, b=b, c=c),
    deband(og_clip=scaled)
)
main_filter = filter_chain(src)


out = main_filter
final = depth(out, 10)
final.set_output()
