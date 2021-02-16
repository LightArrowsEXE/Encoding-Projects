import os
from functools import partial
from typing import List, Tuple, Union

import awsmfunc as awsm
import debandshit as dbs
import havsfunc as haf
import kagefunc as kgf
import lvsfunc as lvf
import mvsfunc as mvf
import vapoursynth as vs
from finedehalo import fine_dehalo
from vardefunc import diff_creditless_mask as DCM
from vsTAAmbk import TAAmbk
from vsutil import depth, get_y, insert_clip, iterate

core = vs.core
core.max_cache_size = 1024 * 32
core.num_threads = 16


shader = 'FSRCNNX_x2_56-16-4-1.glsl'
if os.path.exists(shader) is False:
    hookpath = r"mpv/shaders/FSRCNNX_x2_56-16-4-1.glsl"
    shader = os.path.join(os.getenv("APPDATA"), hookpath)


both = dict(coordinates=[0, 1, 0, 1, 1, 0, 1, 0])


def ringing_mask(clip, rad=4, ethr1=30 << 8, ethr2=50 << 8, minthr=0.5):
    """
    Zastin I love you
    """
    prew = clip.std.Prewitt()
    mask_lo = prew.std.Binarize(ethr1)
    mask_hi = prew.std.Binarize(ethr2)
    main = core.std.Expr([mask_lo, mask_hi.std.Maximum().std.Maximum(), mask_hi], 'x y - z max')
    main = main.std.Maximum().std.Maximum().std.Minimum().std.Minimum()
    shrink = main.std.Minimum()
    lines = core.std.Expr(
        [clip.std.Maximum(**both).std.Maximum(**both).std.Minimum(**both).std.Minimum(**both), clip], 'x y -') \
        .std.Binarize(10 << 8)
    mask = core.std.Expr([main, shrink.std.Maximum(), main.std.Merge(shrink, minthr), lines], 'x y 0 = and x z ? a max')
    imask = iterate(mask, core.std.Maximum, rad).std.Invert()
    return core.std.Expr([mask, imask], 'x y +')


def median(*clips): return core.std.Expr(clips, 'x y z min max y z max min')
def mergechroma(luma, chroma): return core.std.ShufflePlanes([luma, chroma], [0, 1, 2], vs.YUV)


def fader(clip: vs.VideoNode,
          values: Tuple[int, int, int, int] = None
          ) -> vs.VideoNode:
    """
        A fading function that uses kgf.crossfade to fade given clips.
    """
    for start_frame, end_frame, length, input_frame in values:
        clip = insert_clip(clip, kgf.crossfade(clip[start_frame]
                           * length, clip[end_frame] * length, length - 1),
                           input_frame)
    return clip


def replace_section(clip: vs.VideoNode,
                    width: int, height: int,
                    offset_x: int, offset_y: int,
                    ranges: List[Union[int, Tuple[int, int]]],
                    start: int, offset: int) -> vs.VideoNode:
    """
        Replaces a section in the given clip, using a squaremask.
        It takes a given clip, grabs a single frame
        based off the start and the offset.
        It then replaces parts of the clip using lvf.misc.replace_ranges.
    """
    sqmask = kgf.squaremask(clip, width, height, offset_x, offset_y)
    masked = core.std.MaskedMerge(clip, clip[start-offset], sqmask)
    return lvf.misc.replace_ranges(clip, masked, ranges)


def replace_sqmask(clip_a: vs.VideoNode,
                   clip_b: vs.VideoNode,
                   width: int,
                   height: int,
                   offset_x: int,
                   offset_y: int,
                   ranges: List[Union[int, Tuple[int, int]]]
                   ) -> vs.VideoNode:
    """
        Replaces parts of a given clip's given frame, using a squaremask.
        Squaremasks are used to replace parts of the frame.
    """
    sqmask = kgf.squaremask(clip_a, width, height, offset_x, offset_y)
    masked = core.std.MaskedMerge(clip_a, clip_b, sqmask)
    return lvf.misc.replace_ranges(clip_a, masked, ranges)


# Squaremasks
sqmask = []

# Replace BG Elements
replace_bg = []

# Fix fades with heavy banding
fade_fix = []

# Interpolate specific scenes with shimmering
interp_scene = []

# Replace GER signs with JP Signs
aa_credits = [(6246, 6341), (31765, 31884), (34043, 34304), (34578, 34758)]
JP_signs = [(2839, 2897), (6246, 6341), (21460, 21487), (25073, 25371), (31765, 31884), (34043, 34304), (34578, 34758)]

# First OP & ED frames
opstart = 672
edstart = 31885

# Arguments for repeated functions
deband_args = dict(iterations=2, threshold=4, radius=18)
upscaled_args = dict(height=[716, 720], kernel=lvf.kernels.Bilinear())


src_ger = lvf.misc.source(r'BDMV/[BDMV]Clannad/CLANNAD VOLUME 2/BDMV/STREAM/00000.m2ts')[24:-24]
src_jp = lvf.misc.source(r'BDMV/[KUNO-DIY][BDMV][CLANNAD][Blu-ray BOX Disc 1-5 Fin]/CLANNAD_2/BDMV/STREAM/00001.m2ts')[:-48]

if opstart is not None:
    src_NCOP = lvf.src(r'BDMV/[BDMV]Clannad/CLANNAD VOLUME 3/BDMV/STREAM/00013.m2ts')[24:-25]
if edstart is not None:
    src_NCED = lvf.src(r'BDMV/[BDMV]Clannad/CLANNAD VOLUME 3/BDMV/STREAM/00010.m2ts')[24:-25]


# GER BD is overall of higher quality, but replaced quite a few signs
src = lvf.misc.replace_ranges(src_ger, src_jp, ranges=JP_signs)

op_mask = DCM(src, src[opstart:opstart+2154], src_NCOP, opstart, opstart+src_NCOP.num_frames) \
    if opstart is not None else core.std.BlankClip(src)
ed_mask = DCM(src, src[edstart:edstart+2158], src_NCED, edstart, edstart+src_NCED.num_frames) \
    if edstart is not None else core.std.BlankClip(src)
credit_mask = core.std.Expr([get_y(op_mask), get_y(ed_mask)], expr='x y +')
credit_mask = depth(credit_mask, 32)


if sqmask:  # Fix certain frames with other fixes and signs
    for width, height, x, y, ranges in sqmask:
        src = replace_sqmask(src, src_jp, width, height, x, y, ranges)

if replace_bg:  # Fix certain frames with background issues, if applicable.
    for width, height, x, y, ranges, start, offset in replace_bg:
        src = replace_section(src, width, height, x, y, ranges, start, offset)


b = core.std.BlankClip(src)[0]
scomp = lvf.comparison.stack_compare(src_jp+b, src+b, make_diff=True)
ef = awsm.bbmod(src, 1, 1, 1, 1, thresh=40, u=False, v=False)
ef = depth(ef, 32)


lmask = lvf.util.quick_resample(ef, kgf.retinex_edgemask)
lmask = iterate(lmask, core.std.Inflate, 2)
scaled = lvf.scale.descale(ef, mask=None, **upscaled_args)
sraa = lvf.sraa(scaled, rfactor=1.8, downscaler=lvf.kernels.Bicubic().scale, opencl=True)
sraa = core.std.MaskedMerge(ef, sraa, lmask)

dehalo = fine_dehalo(sraa, ref=ef, thmi=48, thma=192)

# The credits look fine, but the preview and episode titles are heavily aliased
strong_aa = lvf.misc.replace_ranges(
    ef, lvf.util.quick_resample(ef, partial(TAAmbk, aatype='Eedi3')),
    ranges=aa_credits
)

title_mask = lvf.scale.descale(
    get_y(ef), mask=partial(lvf.scale.descale_detail_mask, threshold=.12),
    show_mask=True, **upscaled_args
)

# We're also masking the credits in the OP/ED by using the NCs as reference
# Masking credits using NCs
merge = core.std.MaskedMerge(dehalo, strong_aa, title_mask)
merge = core.std.MaskedMerge(merge, ef, credit_mask)
merge = depth(merge, 16)

# Interpolation for some scenes with shimmering
if interp_scene:
    interp = haf.QTGMC(merge, InputType=1, TR0=1, TR1=2, TR2=3, Preset="Very Slow")
    interp = lvf.rfs(merge, interp, ranges=interp_scene)
else:
    interp = merge

recon = lvf.recon.chroma_reconstruct(interp)

ref = haf.SMDegrain(recon, tr=1, thSAD=100, prefilter=3, search=3)
denoise = mvf.BM3D(recon, ref=ref, sigma=[0.4, 0.7], profile1='lc')


den = mvf.BM3D(denoise, sigma=6)
diff_den = core.std.MakeDiff(denoise, den)

detail_mask = lvf.mask.detail_mask(denoise, sigma=0.7, brz_a=0.012, brz_b=0.015)
deband = dbs.f3kpf(den, range=13, y=56, cb=40, cr=40)
deband = core.std.MaskedMerge(deband, den, detail_mask)
deband = core.std.MergeDiff(deband, diff_den)

# Some fades have heavy banding. Fading it myself should fix most of that.
fade = fader(deband, values=fade_fix)
grain = kgf.adaptive_grain(fade, 0.2, luma_scaling=4)


out = grain
final = depth(out, 10)
final.set_output()


if __name__ == '__vapoursynth__':
    import ntpath
    import os

    import kagefunc as kgf

    def keyframes(clip: vs.VideoNode, kf_path: str):
        if not os.path.isdir("keyframes"):
            os.makedirs("keyframes")
        kgf.generate_keyframes(clip, out_path=kf_path, header=False)

    kf_path = f"keyframes/{ntpath.basename(__file__)[:-4]}_keyframes.txt"
    if not os.path.isfile(kf_path):
        keyframes(src, kf_path)
