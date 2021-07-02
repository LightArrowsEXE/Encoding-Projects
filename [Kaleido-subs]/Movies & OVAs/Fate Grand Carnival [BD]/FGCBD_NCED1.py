import os
from typing import List, Tuple, Union

import vapoursynth as vs
from bvsfunc.util import ap_video_source
from lvsfunc.misc import source
from vardautomation import (JAPANESE, AudioStream, FileInfo, Mux, PresetAAC,
                            PresetBD, RunnerConfig, SelfRunner, VideoStream,
                            VPath, X265Encoder)

from fgc_filters import filters as flt

core = vs.core
core.num_threads = 16


# Sources
JP_BD = FileInfo(r'BDMV/BD_VIDEO/BDMV/STREAM/00005.m2ts', 24, -24,
                 idx=lambda x: source(x, force_lsmas=True, cachedir=''),
                 preset=[PresetBD, PresetAAC])
JP_BD.name_file_final = VPath(fr"premux/{JP_BD.name} (Premux).mkv")
JP_BD.a_src_cut = VPath(f"{JP_BD.name}_cut.aac")
JP_BD.do_qpfile = True


def main() -> Union[vs.VideoNode, Tuple[vs.VideoNode, ...]]:
    """Vapoursynth filtering"""
    from vardefunc.noise import decsiz
    from vsutil import get_y

    src = JP_BD.clip_cut
    panorama = flt.panner_x(src, JP_BD.workdir.to_str() + r"/assets/ED/FGCBD_NCED1_panorama.png")

    denoise = decsiz(panorama, min_in=164 << 8, max_in=204 << 8)
    grain = flt.grain(denoise, strength=0.2, luma_scaling=6)

    mask = core.std.Expr(get_y(panorama), f"x {233 << 8} > {255 << 8} 0 ?")
    mask = core.morpho.Close(mask, size=3).std.Minimum().std.Minimum()
    mask = mask.std.Convolution(matrix=[1, 1, 1, 1, 1, 1, 1, 1, 1]) \
        .std.Convolution(matrix=[1, 1, 1, 1, 1, 1, 1, 1, 1]) \
        .std.Convolution(matrix=[1, 1, 1, 1, 1, 1, 1, 1, 1]) \
        .std.Convolution(matrix=[1, 1, 1, 1, 1, 1, 1, 1, 1])

    wh = core.std.BlankClip(grain).std.Invert()
    masked = core.std.MaskedMerge(grain, wh, mask)

    return masked


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

        ap_video_source(self.file.path.to_str(),
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
