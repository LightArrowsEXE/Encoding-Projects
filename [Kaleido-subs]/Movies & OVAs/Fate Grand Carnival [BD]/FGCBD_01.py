import os
from typing import List, Optional, Tuple, Union

import vapoursynth as vs
from bvsfunc.util import ap_video_source
from lvsfunc.misc import source
from lvsfunc.types import Range
from vardautomation import (JAPANESE, AudioStream, FileInfo, Mux, PresetAAC,
                            PresetBD, RunnerConfig, SelfRunner, VideoStream,
                            VPath, X265Encoder)

from fgc_filters import filters as flt

core = vs.core
core.num_threads = 16


shader = r'assets/FSRCNNX_x2_56-16-4-1.glsl'
if os.path.exists(shader) is False:
    hookpath = r"mpv/shaders/FSRCNNX_x2_56-16-4-1.glsl"
    shader = os.path.join(str(os.getenv("APPDATA")), hookpath)


# Sources
JP_BD = FileInfo(r'BDMV/BD_VIDEO/BDMV/STREAM/00003.m2ts', None, -24,
                 idx=lambda x: source(x, force_lsmas=True, cachedir=''),
                 preset=[PresetBD, PresetAAC])
NCOP = FileInfo(r'BDMV/BD_VIDEO/BDMV/STREAM/00004.m2ts', 24, -24,
                idx=lambda x: source(x, force_lsmas=True, cachedir=''))
NCED = FileInfo(r'BDMV/BD_VIDEO/BDMV/STREAM/00005.m2ts', 24, -24,
                idx=lambda x: source(x, force_lsmas=True, cachedir=''))
JP_BD.name_file_final = VPath(fr"premux/{JP_BD.name} (Premux).mkv")
JP_BD.a_src_cut = VPath(f"{JP_BD.name}_cut.aac")
JP_BD.do_qpfile = True


# Common variables
# OP/ED frames
opstart = 1425
edstart = 39795

op_offset = 1
ed_offset = 1


# Scenefiltering
str_deband: List[Range] = [  # Ranges for stronger debanding
    (3583, 3896), (5934, 5971), (8455, 8493), (10517, 10540), (11178, 11336), (11754, 11867), (13022, 13057),
    (16854, 16989), (17415, 17418), (17502, 17594), (18553, 18698), (21699, 21827), (21950, 22003), (21346, 21387),
    (32593, 32700), (39230, 39253), (39486, 39557)
]

aa_ranges: List[Range] = [  # Ranges for stronger AA
    (8455, 8493), (8734, 8786), (8968, 9152), (11616, 11663), (11754, 11867), (14641, 15246), (17422, 17501),
    (17651, 17791), (24187, 24358), (20392, 20531), (38734, 38829)
]

no_descale: List[Range] = [  # Faster to encode if we just don't descale
    (42926, 43131)
]


str_grain_ranges: List[Range] = [  # Stronger graining ranges
    (21346, 21387), (36514, 36645), (39155, 39202)
]

op_replace: List[int] = [  # Frame before it gets replaced  #noqa
]


if opstart is not None:
    str_deband += [(opstart+572, opstart+590), (opstart+731, opstart+748), (opstart+1360, opstart+1379)]
    aa_ranges += [(opstart+626, opstart+697), (opstart+824, opstart+889), (opstart+1387, opstart+1416)]
    op_replace += op_replace + [opstart+857]


def main() -> Union[vs.VideoNode, Tuple[vs.VideoNode, ...]]:
    """Vapoursynth filtering"""
    # Don't worry, this script is barely readable anymore even for me
    import rekt
    from awsmfunc import bbmod
    from havsfunc import ContraSharpening
    from lvsfunc.aa import upscaled_sraa
    from lvsfunc.comparison import stack_compare
    from lvsfunc.mask import BoundingBox
    from lvsfunc.util import replace_ranges
    from vardefunc import dcm
    from vardefunc.deband import dumb3kdb
    from vardefunc.mask import FreyChen
    from vsutil import depth, get_y, insert_clip

    src = JP_BD.clip_cut
    b = core.std.BlankClip(src, length=1)

    if opstart is not False:
        src_NCOP = NCOP.clip_cut
        op_scomp = stack_compare(src[opstart:opstart+src_NCOP.num_frames-1]+b, src_NCOP[:-op_offset]+b, make_diff=True)  # noqa
    if edstart is not False:
        src_NCED = NCED.clip_cut
        #ed_scomp = stack_compare(src[edstart:edstart+src_NCED.num_frames-1]+b, src_NCED[:-ed_offset]+b, make_diff=True)  # noqa

    # Masking credits
    op_mask = dcm(
        src, src[opstart:opstart+src_NCOP.num_frames], src_NCOP,
        start_frame=opstart, thr=25, prefilter=True) if opstart is not False \
        else get_y(core.std.BlankClip(src))
    ed_mask = dcm(
        src, src[edstart:edstart+src_NCED.num_frames], src_NCED,
        start_frame=edstart, thr=25, prefilter=True) if edstart is not False \
        else get_y(core.std.BlankClip(src))
    credit_mask = core.std.Expr([op_mask, ed_mask], expr='x y +')
    credit_mask = depth(credit_mask, 16).std.Binarize()

    # Fixing an animation fuck-up
    for f in op_replace:
        src = insert_clip(src, src[f], f-1)

    # Edgefixing
    ef = rekt.rektlvls(
        src, prot_val=[16, 235], min=16, max=235,
        rownum=[0, src.height-1], rowval=[16, 16],
        colnum=[0, src.width-1], colval=[16, 16],
    )

    bb_y = bbmod(ef, left=1, top=1, right=1, bottom=1, thresh=32, y=True, u=False, v=False)
    bb_uv = bbmod(bb_y, left=2, top=2, right=2, bottom=2, y=False, u=True, v=True)
    bb32 = depth(bb_uv, 32)

    # --- Very specific filtering that should probably be removed for future episodes entirely
    # Fading for some... well, fades.
    fade = flt.fader(bb32, start_frame=4437, end_frame=4452)
    fade = flt.fader(fade, start_frame=18660, end_frame=18697)

    # Different sport names
    rkt_aa_ranges: Union[Union[int, None, Tuple[Optional[int], Optional[int]]], List[Union[int, None, Tuple[Optional[int], Optional[int]]]], None] = [  # noqa
        (8824, 8907), (9828, 9911), (10995, 11078), (11904, 12010)
    ]

    rkt_aa = rekt.rekt_fast(fade, fun=lambda x: upscaled_sraa(x), top=854, left=422, bottom=60, right=422)
    rkt_aa = replace_ranges(fade, rkt_aa, rkt_aa_ranges)

    # QP GET!
    rkt_aa2_ranges: Union[Union[int, None, Tuple[Optional[int], Optional[int]]], List[Union[int, None, Tuple[Optional[int], Optional[int]]]], None] = [  # noqa
        (26333, 26333), (28291, 28344), (30271, 30364)
    ]
    rkt_aa2 = rekt.rekt_fast(rkt_aa, fun=lambda x: upscaled_sraa(x), top=714, left=354, bottom=224, right=354)
    rkt_aa2 = replace_ranges(fade, rkt_aa, rkt_aa2_ranges)

    # Table stuff
    rkt_aa3_ranges: Union[Union[int, None, Tuple[Optional[int], Optional[int]]], List[Union[int, None, Tuple[Optional[int], Optional[int]]]], None] = [  # noqa
        (32797, 32952)
    ]
    rkt_aa3 = rekt.rekt_fast(rkt_aa2, fun=lambda x: upscaled_sraa(x), top=488, left=312, bottom=390, right=850)
    rkt_aa3 = replace_ranges(fade, rkt_aa2, rkt_aa3_ranges)

    rkt_aa = rkt_aa3

    # Clipping error Nyatalante/Achilles
    fixed_frame = source(JP_BD.workdir.to_str() + r"/assets/01/FGCBD_01_8970_fixed.png", rkt_aa)
    fix_error = replace_ranges(rkt_aa, fixed_frame, [(8968, 8970)])

    sp_out32 = fix_error
    sp_out16 = depth(sp_out32, 16)

    # Rescaling
    l_mask = FreyChen().get_mask(get_y(sp_out16)).morpho.Close(size=6)
    l_mask = core.std.Binarize(l_mask, 24 << 8).std.Maximum().std.Maximum()
    scaled, credit_mask = flt.rescaler(sp_out32, height=720, shader_file=shader)
    scaled = core.std.MaskedMerge(sp_out16, scaled, l_mask)
    scaled = core.std.MaskedMerge(scaled, sp_out16, credit_mask)

    # Denoising
    denoise = flt.multi_denoise(scaled, l_mask)

    # Anti-aliasing
    aa_clamped = flt.clamp_aa(denoise, strength=3.0)
    aa_rfs = replace_ranges(denoise, aa_clamped, aa_ranges)

    # Fix edges because they get fucked during the denoising and AA stages
    box = BoundingBox((1, 1), (src.width-2, src.height-2))
    fix_edges = core.std.MaskedMerge(scaled, aa_rfs, box.get_mask(scaled))

    # Regular debanding, but then...
    deband = flt.multi_debander(fix_edges, sp_out16)

    # --- More very specific filtering that should almost definitely be removed for other episodes
    boxes = [
        BoundingBox((0, 880), (1920, 200)),
        BoundingBox((1367, 0), (552, 1080)),
        BoundingBox((1143, 0), (466, 83)),
        BoundingBox((1233, 84), (237, 84)),
    ]

    boxed_deband = flt.placebo_debander(fix_edges, iterations=2, threshold=8, radius=14, grain=4)
    boxed_mask = core.std.BlankClip(boxed_deband.std.ShufflePlanes(planes=0, colorfamily=vs.GRAY))
    for bx in boxes:  # Gonna be awfully slow but OH WELLLLLL
        boxed_mask = core.std.Expr([boxed_mask, bx.get_mask(boxed_mask)], "x y max")

    boxed_deband_merged = core.std.MaskedMerge(deband, boxed_deband, boxed_mask)
    boxed_deband_merged = replace_ranges(deband, boxed_deband_merged, [(20554, 20625)])

    stronger_deband = dumb3kdb(fix_edges, radius=18, threshold=[48, 32])
    stronger_deband = replace_ranges(boxed_deband_merged, stronger_deband, [
        (22547, 22912), (28615, 28846), (33499, 33708), (37223, 37572), (37636, 37791), (38047, 38102), (38411, 38733)]
    )

    deband_csharp = ContraSharpening(stronger_deband, scaled, 17)

    sp_out = deband_csharp

    # Back to regular graining
    grain = flt.grain(sp_out)

    return grain


def output(clip: vs.VideoNode) -> vs.VideoNode:
    """Dithering down and setting TV range for the output video node"""
    from vsutil import depth

    return depth(clip, 10).std.Limiter(16 << 2, [235 << 2, 240 << 2], [0, 1, 2])

XML_TAG = "settings/tags_aac.xml"


class Encoding:
    def __init__(self, file: FileInfo, clip: vs.VideoNode) -> None:
        self.file = file
        self.clip = clip

    def run(self) -> None:
        assert self.file.a_src
        assert self.file.a_src_cut

        v_encoder = X265Encoder('settings/x265_settings_BD')

        ap_video_source(self.file.path_without_ext.to_str() + ".mkv",  # mkv because >chapters first and begna's code breaks
                        [self.file.frame_start, self.file.frame_end],
                        framerate=self.clip.fps,
                        noflac=True, noaac=False, nocleanup=False, silent=False)
        os.rename(self.file.path_without_ext.to_str() + "_2_cut.aac", self.file.a_src_cut.to_str())

        muxer = Mux(
            self.file,
            streams=(
                VideoStream(self.file.name_clip_output, 'HEVC BDrip by LightArrowsEXE@Kaleido', JAPANESE),
                AudioStream(self.file.a_src_cut.format(1), 'AAC 2.0', JAPANESE, XML_TAG),
                None
            )
        )

        config = RunnerConfig(v_encoder, None, None, None, None, muxer)

        runner = SelfRunner(self.clip, self.file, config)
        runner.run()
        runner.do_cleanup(XML_TAG)


if __name__ == '__main__':
    filtered = main()
    filtered = output(filtered)  # type: ignore
    Encoding(JP_BD, filtered).run()
elif __name__ == '__vapoursynth__':
    filtered = main()
    if not isinstance(filtered, vs.VideoNode):
        raise RuntimeError("Multiple output nodes were set when `vspipe` only expected one")
    else:
        filtered.set_output(0)
else:
    JP_BD.clip_cut.set_output(0)
    FILTERED = main()
    if not isinstance(FILTERED, vs.VideoNode):
        for i, clip_filtered in enumerate(FILTERED, start=1):
            clip_filtered.set_output(i)
    else:
        FILTERED.set_output(1)
