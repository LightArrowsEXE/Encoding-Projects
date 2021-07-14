import argparse  # noqa
import os
from typing import List, Optional, Tuple, Union

import vapoursynth as vs
from bvsfunc.util import ap_video_source
from lvsfunc.misc import source
from lvsfunc.types import Range
from vardautomation import (JAPANESE, AudioStream, FileInfo, Mux, PresetAAC,
                            PresetWEB, RunnerConfig, SelfRunner, VideoStream,
                            VPath, X264Encoder)

from kobayashi2_filters import flt, util

core = vs.core

EP_NUM = __file__[-5:-3]


# Sources
JP_CR = FileInfo(f'sources/{EP_NUM}/Kobayashi-san Chi no Maid Dragon S E{EP_NUM} [1080p][AAC][JapDub][GerEngSub][Web-DL].mkv',
                 idx=lambda x: source(x, force_lsmas=True, cachedir=''))
JP_AOD = FileInfo(f'sources/{EP_NUM}/Kobayashi-san Chi no Maid Dragon S E{EP_NUM} [1080p+][AAC][JapDub][GerSub][Web-DL].mkv',
                  idx=lambda x: source(x, force_lsmas=True, cachedir=''),
                  preset=[PresetWEB, PresetAAC])
YT_NCOP = FileInfo('sources/【期間限定公開】TVアニメ『小林さんちのメイドラゴンＳ』ノンテロップオープニング映像-bEb4xT8lnYU.mkv',
                   idx=lambda x: source(x, force_lsmas=True, cachedir=''))
YT_NCED = FileInfo('sources/【期間限定公開】TVアニメ『小林さんちのメイドラゴンＳ』ノンテロップエンディング映像-kMWLe37SMBs.mp4',
                   idx=lambda x: source(x, force_lsmas=True, cachedir=''))
JP_AOD.name_file_final = VPath(fr"Premux/Kobayashi-san Chi no Maid Dragon S - {EP_NUM} (Premux).mkv")
JP_AOD.name_clip_output = VPath(JP_AOD.name + '.264')
JP_AOD.a_src_cut = VPath(f"{JP_AOD.name}_cut.aac")
JP_AOD.do_qpfile = True


# Common variables
# OP/ED frames
opstart = 1128
edstart = 31409
op_offset = 3
ed_offset = 3

hardsub_sign: List[Range] = [  # Leftover hardsubbed signs that need a stronger mask
    (10872, 10932), (20858, 20885), (25963, 25979), (26772, 26778), (27002, 27008), (27366, 27372), (27531, 27537),
    (27585, 27605), (33566, 33625)
]

replace_scenes: List[Range] = [  # List of scenes to replace
]


def trim() -> Tuple[vs.VideoNode, Optional[vs.VideoNode], vs.VideoNode]:
    """Waka/Aod trimming"""
    from lvsfunc.comparison import diff, stack_compare  # noqa

    src_clean = JP_CR.clip_cut
    src_hard = JP_AOD.clip_cut
    hdiff = None

    dehardsubbed = util.dehardsub(src_hard, src_clean, hardsub_sign, replace_scenes)
    scomp = stack_compare(src_clean, dehardsubbed)

    # Comment out after it's run because >lol wasting time in $(CURRENT YEAR)
    #hdiff = diff(src_clean, dehardsubbed, thr=80)

    return dehardsubbed, hdiff, scomp


def filterchain() -> Union[vs.VideoNode, Tuple[vs.VideoNode, ...]]:
    """Regular VapourSynth filtering"""
    import lvsfunc as lvf
    import vardefunc as vdf
    from vsutil import depth, get_y

    src, *_ = trim()
    src_CR = JP_CR.clip_cut
    src_NCOP, src_NCED = YT_NCOP.clip, YT_NCED.clip
    b = core.std.BlankClip(src, length=1)

    # OP/ED stack comps to check that it lines up
    op_scomp = lvf.scomp(src[opstart:opstart+src_NCOP.num_frames-1]+b, src_NCOP[:-op_offset]+b)  # noqa
    ed_scomp = lvf.scomp(src[edstart:edstart+src_NCED.num_frames-1]+b, src_NCED[:-ed_offset]+b)  # noqa

    # Blurring clips
    blur_src = core.bilateral.Gaussian(src, sigma=2.5)
    blur_NCOP = core.bilateral.Gaussian(src_NCOP, sigma=2.5)
    blur_NCED = core.bilateral.Gaussian(src_NCED, sigma=2.5)

    # Masking credits
    op_mask = vdf.dcm(
        blur_src, blur_src[opstart:opstart+src_NCOP.num_frames-op_offset], blur_NCOP[:-op_offset],
        start_frame=opstart, thr=28, prefilter=False) if opstart is not False \
        else get_y(core.std.BlankClip(src))
    ed_mask = vdf.dcm(
        blur_src, blur_src[edstart:edstart+src_NCED.num_frames-ed_offset], blur_NCED[:-ed_offset],
        start_frame=edstart, thr=25, prefilter=False) if edstart is not False \
        else get_y(core.std.BlankClip(src))
    credit_mask = core.std.Expr([op_mask, ed_mask], expr='x y +')
    credit_mask = depth(credit_mask, 16).std.Binarize()

    return credit_mask

    # This time, AoD has better lines but worse gradients (over-debanded + super grained),
    # but only on certain dark and texture-heavy (but low-motion) scenes, but ugh effort
    line_mask = vdf.mask.FDOG().get_mask(get_y(src))
    src_merge = core.std.MaskedMerge(src_CR, src, line_mask)
    src_merge = lvf.rfs(src, src_merge, [(2637, 2722), (10933, 10978), (11388, 11479), (13058, 13406), (13539, 14029), (14052, 14300), (14422, 14560)])

    src_merge = depth(src_merge, 16)

    src_y = get_y(src_merge)
    denoise_y = flt.bm3d_ref(src_y, bm3d_sigma=1, dec_sigma=8, dec_min=192 << 8)
    denoise_y = core.std.MaskedMerge(denoise_y, src_y, depth(line_mask, 16))
    merged = vdf.misc.merge_chroma(denoise_y, src_merge)

    dehalo = flt.bidehalo(merged, sigma=1, mask_args={'brz': 0.25})

    cmerged = core.std.MaskedMerge(dehalo, src_merge, credit_mask)

    deband = flt.masked_f3kdb(cmerged, thr=20, grain=12, mask_args={'brz': (1500, 3500)})
    grain = flt.default_grain(deband)

    return grain  # type: ignore


def wraw() -> vs.VideoNode:
    """Workraw filtering. Kept as light as reasonably possible for speed"""
    from vsutil import depth

    src, _, _ = trim()
    src = depth(src, 16)

    deband = flt.masked_f3kdb(src, thr=30, grain=16, mask_args={'brz': (1500, 3500)})
    grain = flt.default_grain(deband)

    return grain  # type: ignore


def output(clip: vs.VideoNode) -> vs.VideoNode:
    """Dithering down and settings TV range for the output video node"""
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

        if run_wraw:
            v_encoder = X264Encoder('settings/x264_settings_wraw')
        else:
            v_encoder = X264Encoder('settings/x264_settings')

        audio_files = ap_video_source(self.file.path.to_str(),
                                      [self.file.frame_start, self.file.frame_end],
                                      framerate=self.clip.fps,
                                      noflac=True, noaac=False, nocleanup=False, silent=False)

        audio_tracks: List[AudioStream] = []
        for track in audio_files:
            audio_tracks += [AudioStream(track[0], 'AAC 2.0', JAPANESE, XML_TAG)]
        print(audio_tracks)

        muxer = Mux(
            self.file,
            streams=(
                VideoStream(self.file.name_clip_output, 'h264 WEBrip by LightArrowsEXE@DameDesuYo', JAPANESE),
                audio_tracks,
                None
            )
        )

        config = RunnerConfig(v_encoder, None, None, None, None, muxer)

        runner = SelfRunner(self.clip, self.file, config)
        runner.run()
        # runner.do_cleanup()


if __name__ == '__main__':
    # This breaks `runner.run()` and I have no idea why.
    # Just set the flag yourself manually until I fix this.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-W", "--wraw",
                        action="store_true", default=False,
                        help="Encode a work raw instead of a regular raw")
    args = parser.parse_args()
    """

    run_wraw = False

    if run_wraw:
        print(f"Warning: Encoding work raw of {os.path.basename(__file__)}")
        JP_AOD.name_file_final = VPath(fr"wraws/{JP_AOD.name} (work raw).mkv")
        JP_AOD.name_clip_output = VPath(JP_AOD.name + '_wraw.264')
        filtered = wraw()
    else:
        print("Running regular encode")
        filtered = filterchain()  # type: ignore

    filtered = output(filtered)
    Encoding(JP_AOD, filtered).run()
elif __name__ == '__vapoursynth__':
    filtered = filterchain()  # type: ignore
    if not isinstance(filtered, vs.VideoNode):
        for i, clip_filtered in enumerate(filtered, start=1):  # type: ignore
            clip_filtered.set_output(i)
    else:
        filtered.set_output(1)
else:
    JP_CR.clip_cut.set_output(0)
    JP_AOD.clip_cut.set_output(1)
    #FILTERED = trim()
    FILTERED = filterchain()
    if not isinstance(FILTERED, vs.VideoNode):
        for i, clip_filtered in enumerate(FILTERED, start=2):
            if clip_filtered:
                clip_filtered.set_output(i)
    else:
        FILTERED.set_output(2)
