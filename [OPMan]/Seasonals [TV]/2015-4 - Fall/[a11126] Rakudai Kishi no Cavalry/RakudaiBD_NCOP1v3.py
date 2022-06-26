from __future__ import annotations

from typing import Any, Dict, List, Tuple

import vapoursynth as vs
import vsencode as vse
from lvsfunc.types import Range
from vardefunc import initialise_input

from project_module import flt

ini = vse.generate.init_project()

core = vse.util.get_vs_core(reserve_core=ini.reserve_core)

shader = vse.get_shader("FSRCNNX_x2_56-16-4-1.glsl")


# Sources
SRC = vse.FileInfo(f"{ini.bdmv_dir}/RAKUDAI_KISHI_NO_CAVALRY_VOL5/BDROM/BDMV/STREAM/00012.m2ts", (24, -24))


freeze_ranges: List[Range] = [  # Freezeframing and averaging certain stills
    (20, 26), (67, 69), (78, 83), (101, 103), (178, 195), (280, 287), (1124, 1133), (1134, 1142), (1143, 1150),
    (1151, 1159), (1820, 1831), (1832, 1842), (1843, 1861), (2025, 2159)
]

zones: Dict[Tuple[int, int], Dict[str, Any]] = {  # Zones for the encoder
}


@initialise_input(bits=32)
def filterchain(src: vs.VideoNode = SRC.clip_cut) -> vs.VideoNode | Tuple[vs.VideoNode, ...]:
    """Main filterchain"""
    from functools import partial

    import havsfunc as haf
    import jvsfunc as jvf
    import lvsfunc as lvf
    import vardefunc as vdf
    from vsutil import depth, get_w, get_y, insert_clip, iterate

    assert src.format

    freeze_start: List[int] = []
    freeze_end: List[int] = []

    for start, end in freeze_ranges:
        freeze_frames: List[vs.VideoNode] = []
        freeze_start += [start]
        freeze_end += [end]

        end = end + 1

        for i in range(start, end):
            freeze_frames += [src[i]]

        avg = core.average.Mean(freeze_frames)
        src = insert_clip(src, avg * (end - start), start)

    src_y = get_y(src)

    luma_mask = core.akarin.Expr(src_y, f"x {5 / 255} > 0 1 ?")
    luma_mask = iterate(luma_mask, partial(jvf.expr_close, size=15), 2).rgsf.RemoveGrain(4).std.Minimum()
    luma_mask = luma_mask.std.Deflate().std.Inflate().std.Maximum().std.Median().std.Convolution([1] * 9)
    luma_mask = depth(luma_mask, 16).std.Limiter()

    l_mask = vdf.mask.FDOG().get_mask(src_y, lthr=0.175, hthr=0.175).rgsf.RemoveGrain(4).rgsf.RemoveGrain(4)
    l_mask = l_mask.std.Minimum().std.Deflate().std.Median().std.Convolution([1] * 9)

    descale = lvf.kernels.Bicubic(b=.2, c=.4).descale(src_y, get_w(720), 720)
    upscale = vdf.scale.fsrcnnx_upscale(descale, 1920, 1080, shader,
                                        downscaler=lvf.scale.ssim_downsample,
                                        undershoot=1.1, overshoot=1.5)
    upscale_min = core.akarin.Expr([src_y, upscale], "x y min")
    rescale = core.std.MaskedMerge(src_y, upscale_min, l_mask)
    scaled = depth(vdf.misc.merge_chroma(rescale, src), 16)

    smd = haf.SMDegrain(scaled, tr=5, thSAD=50)
    dft = core.dfttest.DFTTest(smd, sigma=6)
    dft = core.std.MaskedMerge(smd, dft, luma_mask)
    ccd_uv = jvf.ccd(dft, threshold=6)
    decs = vdf.noise.decsiz(ccd_uv, min_in=192 << 8, max_in=240 << 8)

    aa = lvf.sraa(decs)
    aa = lvf.rfs(decs, aa, [(2025, None)])

    deband = flt.masked_f3kdb(aa, rad=18, thr=[24, 12], grain=[24, 12])

    freeze = deband.std.FreezeFrames(  # Optimisations by creating pointers for still shots
        freeze_start, freeze_end, freeze_start
    )

    return freeze


FILTERED = filterchain()


if __name__ == '__main__':
    vse.EncodeRunner(SRC, FILTERED).video('x265', 'settings/x265_settings', zones=zones) \
        .audio('flac').mux('LightArrowsEXE@Kaleido').run()
elif __name__ == '__vapoursynth__':
    if not isinstance(FILTERED, vs.VideoNode):
        raise vs.Error(f"Input clip has multiple output nodes ({len(FILTERED)})! Please output a single clip")
    else:
        vse.video.finalize_clip(FILTERED).set_output(0)
else:
    SRC.clip_cut.set_output(0)

    if not isinstance(FILTERED, vs.VideoNode):
        for i, clip_filtered in enumerate(FILTERED, start=1):
            clip_filtered.set_output(i)
    else:
        FILTERED.set_output(1)

    for i, audio_node in enumerate(SRC.audios_cut, start=10):
        audio_node.set_output(i)
