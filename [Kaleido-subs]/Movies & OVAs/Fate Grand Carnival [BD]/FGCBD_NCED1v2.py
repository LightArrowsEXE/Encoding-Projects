import os
import re
from functools import partial
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple, Union

import vapoursynth as vs
from lvsfunc.misc import source
from lvsfunc.types import Range
from vardautomation import FileInfo, PresetAAC, PresetBD, VPath

from project_module import enc, flt

core = vs.core


shader_file = 'assets/FSRCNNX_x2_16-0-4-1.glsl'
if not Path(shader_file).exists():
    hookpath = r"mpv/shaders/FSRCNNX_x2_16-0-4-1.glsl"
    shader_file = os.path.join(str(os.getenv("APPDATA")), hookpath)


# Sources
JP_BD = FileInfo(r'BDMV/02/BD_VIDEO/BDMV/STREAM/00005.m2ts', (24, -24),
                 idx=lambda x: source(x, force_lsmas=True, cachedir=''), preset=[PresetBD, PresetAAC])
JP_BD.name_file_final = VPath(fr"premux/{JP_BD.name} (Premux).mkv")
JP_BD.a_src_cut = VPath(f"{JP_BD.name}_cut.aac")
JP_BD.do_qpfile = True


# Common variables
opstart = 56  # First cut
edstart = False
name = __name__[7:-3]


# Scenefiltering
cshift_left_ranges: Iterable[Range] = [  # Shift chroma to the left
]

freeze_ranges: Iterable[Iterable[int]] = [  # [start_frame, end_frame, frame]
]

no_filter: Iterable[Range] = [  # Ranges that do not get filtered
]


if re.search('v1', __name__) or re.search('01', __name__):
    freeze_ranges += [[opstart+801, opstart+801, opstart+800]]  # Animation fix in NCOP1v1


zones: Dict[Tuple[int, int], Dict[str, Any]] = {  # Zones for x265
}


def pre_filterchain() -> Union[vs.VideoNode, Tuple[vs.VideoNode, ...]]:
    """
    Regular filtering to get the output images to stitch.

    This is preferable over handling it unfiltered, since it'll be faster than encoding it
    and reduces the amount of jitter caused by the upscale after.
    """
    import lvsfunc as lvf
    import rekt
    import vardefunc as vdf
    from awsmfunc import bbmod
    from muvsfunc import SSIM_downsample
    from vsutil import depth, get_y, join, plane

    src = JP_BD.clip_cut

    # Fixing animation fuck-ups
    if freeze_ranges:
        src = core.std.FreezeFrames(
            src,
            [s[0] for s in freeze_ranges],
            [e[1] for e in freeze_ranges],
            [f[2] for f in freeze_ranges]
        )

    # Edgefixing
    ef = rekt.rektlvls(
        src, prot_val=[16, 235], min=16, max=235,
        rownum=[0, src.height-1], rowval=[16, 16],
        colnum=[0, src.width-1], colval=[16, 16],
    )

    bb_y = bbmod(ef, left=1, top=1, right=1, bottom=1, thresh=32, y=True, u=False, v=False)
    bb_uv = bbmod(bb_y, left=2, top=2, right=2, bottom=2, y=False, u=True, v=True)

    cshift = flt.shift_chroma(bb_uv, left=0.6)
    cshift = lvf.rfs(bb_uv, cshift, cshift_left_ranges)

    bb32 = depth(cshift, 32)
    bb32_y = get_y(bb32)

    # Descaling + DPIR while it's at a lower res (so I can actually run it because >memory issues xd)
    descale = lvf.kernels.Catrom().descale(bb32_y, 1280, 720)
    downscale = lvf.kernels.Catrom(format=vs.YUV444PS).scale(bb32, 1280, 720)
    descale_444 = join([descale, plane(downscale, 1), plane(downscale, 2)])
    denoise_y = lvf.deblock.vsdpir(descale_444, strength=2.75, mode='deblock', matrix=1, i444=True, cuda=True)

    supersample = vdf.scale.fsrcnnx_upscale(get_y(denoise_y), shader_file=shader_file, downscaler=None)
    downscaled = SSIM_downsample(supersample, src.width, src.height, smooth=((3 ** 2 - 1) / 12) ** 0.5,
                                 sigmoid=True, filter_param_a=0, filter_param_b=0)

    # Create credit mask
    upscale = lvf.kernels.Catrom().scale(descale, src.width, src.height)
    credit_mask = lvf.scale.descale_detail_mask(bb32_y, upscale, threshold=0.055) \
        .std.Deflate().std.Deflate().std.Minimum()

    # Merge early for additional accuracy with DPIR
    merged = core.std.MaskedMerge(downscaled, bb32_y, credit_mask)

    down_y = lvf.kernels.Catrom().scale(merged, src.width/2, src.height/2)
    down_i444 = join([down_y, plane(bb32, 1), plane(bb32, 2)])
    deblock_down = lvf.deblock.vsdpir(down_i444, strength=3, mode='denoise', matrix=1, i444=True, cuda=True)

    scaled = depth(join([merged, plane(deblock_down, 1), plane(deblock_down, 2)]), 16)

    # Final bit of "denoising"
    dft = core.dfttest.DFTTest(scaled, sigma=2.0, tbsize=5, tosize=3, planes=[0])
    decs = vdf.noise.decsiz(dft, sigmaS=4, min_in=208 << 8, max_in=232 << 8)

    # AA
    baa = lvf.aa.based_aa(decs, str(shader_file))
    sraa = lvf.sraa(decs, rfactor=1.65)
    clmp = lvf.aa.clamp_aa(decs, baa, sraa, strength=1.3)

    dehalo = lvf.dehalo.masked_dha(clmp, rx=1.4, ry=1.4, brightstr=0.4)
    cwarp = core.warp.AWarpSharp2(dehalo, thresh=72, blur=3, type=1, depth=4, planes=[1, 2])

    # Merge credits (if applicable)
    merged = core.std.MaskedMerge(cwarp, depth(bb32, 16), depth(credit_mask, 16))

    deband = core.average.Mean([
        flt.masked_f3kdb(merged, rad=16, thr=[20, 24], grain=[24, 12]),
        flt.masked_f3kdb(merged, rad=20, thr=[28, 24], grain=[24, 12]),
        flt.masked_placebo(merged, rad=6, thr=2.5, itr=2, grain=4)
    ])

    no_flt = lvf.rfs(deband, depth(bb32, 16), no_filter)

    return no_flt


def extract_frames() -> bool:
    """We extract every frame here and pass those to Overmix to stitch the pan together again."""
    from project_module.util import extract_frames

    clip = pre_filterchain()
    if not Path(f"assets/{name}/frames/{name}_{clip.num_frames}.png").exists():
        extract_frames(clip, name, 'assets/NCED1v2/frames')

    if not Path(f"assets/{name}/{name}_stitched.png").exists():
        return False
    return True


def final_filterchain() -> vs.VideoNode:
    """Final post-filtering chain"""
    from fractions import Fraction

    import vardefunc as vdf
    from vsutil import get_y, iterate

    if not extract_frames():
        raise vs.Error("Stitched image does not exist!")

    clip = pre_filterchain()
    img = f"assets/{name}/{name}_stitched.png"

    pan = flt.panner_x(clip, img, fps=Fraction(30000/1001))

    denoise = vdf.noise.decsiz(pan, min_in=164 << 8, max_in=204 << 8)
    grain = vdf.noise.Graigasm(
        thrs=[x << 8 for x in (32, 80, 128, 176)],
        strengths=[(0.25, 0.0), (0.20, 0.0), (0.15, 0.0), (0.0, 0.0)],
        sizes=(1.20, 1.15, 1.10, 1),
        sharps=(80, 70, 60, 50),
        grainers=[
            vdf.noise.AddGrain(seed=69420, constant=True),
            vdf.noise.AddGrain(seed=69420, constant=True),
            vdf.noise.AddGrain(seed=69420, constant=True)
        ]).graining(denoise)

    mask = core.std.Expr(get_y(pan), f"x {233 << 8} > {255 << 8} 0 ?")
    mask = mask.std.Maximum().std.Minimum()
    mask = iterate(mask, partial(core.std.Convolution, matrix=[1, 1, 1, 1, 1, 1, 1, 1, 1]), 4)

    wh = core.std.BlankClip(grain).std.Invert()
    masked = core.std.MaskedMerge(grain, wh, mask)

    return masked


if __name__ == '__main__':
    enc.Encoder(JP_BD, final_filterchain()).run(clean_up=True, zones=zones)  # type: ignore
elif __name__ == '__vapoursynth__':
    FILTERED = final_filterchain()
    if not isinstance(FILTERED, vs.VideoNode):
        raise ImportError(f"Input clip has multiple output nodes ({len(FILTERED)})! Please output a single clip")
    else:
        enc.dither_down(FILTERED).set_output(0)
else:
    JP_BD.clip_cut.std.SetFrameProp('node', intval=0).set_output(0)
    # FILTERED = pre_filterchain()
    FILTERED = final_filterchain()
    if not isinstance(FILTERED, vs.VideoNode):
        for i, clip_filtered in enumerate(FILTERED, start=1):
            clip_filtered.std.SetFrameProp('node', intval=i).set_output(i)
    else:
        FILTERED.std.SetFrameProp('node', intval=1).set_output(1)
