import os
from functools import partial
from typing import List, Tuple, Union

import havsfunc as haf
import kagefunc as kgf
import lvsfunc as lvf
import mvsfunc as mvf
from awsmfunc import bbmod
from vardefunc import diff_creditless_mask as DCM
from vsTAAmbk import TAAmbk
from vsutil import depth, get_y, insert_clip, join, plane

import vapoursynth as vs

core = vs.core
core.max_cache_size = 1024 * 224
core.num_threads = 12


shader = 'FSRCNNX_x2_56-16-4-1.glsl'
if os.path.exists(shader) is False:
    hookpath = r"mpv/shaders/FSRCNNX_x2_56-16-4-1.glsl"
    shader = os.path.join(os.getenv("APPDATA"), hookpath)


@lvf.misc.chroma_injector
@lvf.misc.allow_variable(width=1920, height=1080)
def tfsr(clip, width: int = 1920, height: int = 1080) -> vs.VideoNode:
    return clip.resize.Point(format=vs.YUV444P16) \
        .placebo.Shader(width=width*2, height=height*2, shader=shader) \
        .resize.Bicubic(width, height, format=clip.format.id)


def fix_lineart(clip: vs.VideoNode) -> vs.VideoNode:
    """
        A function that performs HQDeringmod with a repair on the lineart.
    """
    dering = lvf.util.quick_resample(
        clip, partial(haf.HQDeringmod, nrmode=1, mrad=2, thr=3, sharp=0)
    )
    return lvf.util.pick_repair(dering)(dering, clip, 13)


# Arguments for repeated functions
deband_args = dict(iterations=2, threshold=4, radius=18)
upscaled_args = dict(height=[716, 720], kernel=lvf.kernels.Bilinear())


src = lvf.src(r'BDMV/[BDMV]Clannad/CLANNAD VOLUME 3/BDMV/STREAM/00013.m2ts')[24:-25]
ef = bbmod(src, 1, 1, 1, 1, thresh=40, blur=999, y=True, u=False, v=False)
ef = depth(ef, 32)


scaled = lvf.scale.descale(ef, upscaler=lambda clip, width, height:
                           tfsr(ef, clip, width, height), mask=None, **upscaled_args) \
            .rgsf.Repair(ef, 13)


aa = lvf.aa.nneedi3_clamp(scaled)
dering = fix_lineart(aa)


# vs-placebo does a pretty aight job of debanding this
detail_mask = lvf.denoise.detail_mask(
    dering, pre_denoise=0.6, brz_a=0.06, brz_b=0.012
)
denoise = mvf.BM3D(dering, sigma=[0.6, 1], profile1='lc')
deband = join([  # For whatever reason this is faster, like ???
            core.placebo.Deband(plane(dering, 0), grain=10, **deband_args),
            core.placebo.Deband(plane(dering, 1), grain=0,  **deband_args),
            core.placebo.Deband(plane(dering, 2), grain=0,  **deband_args)
])
deband = core.std.MaskedMerge(deband, dering, detail_mask)

grain = kgf.adaptive_grain(deband, 0.45, luma_scaling=4)


out = grain
final = depth(out, 10)
final.set_output()
