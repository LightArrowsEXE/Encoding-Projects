import os
from typing import List, Optional, Tuple, Union

import vapoursynth as vs
from bvsfunc.util import ap_video_source
from lvsfunc.misc import source
from lvsfunc.types import Range
from vardautomation import (JAPANESE, AudioStream, FileInfo, Mux, PresetAAC,
                            PresetBD, RunnerConfig, SelfRunner, VideoStream,
                            VPath, X265Encoder)
from vsutil import depth
from gbf2_filters import chain

core = vs.core
core.num_threads = 16


# Sources
JP_BD = FileInfo(r'BDMV/GRANBLUE_FANTASY_SEASON2_1/BDMV/STREAM/00008.m2ts', None, -24,
                 idx=lambda x: source(x, force_lsmas=True, cachedir=''),
                 preset=[PresetBD, PresetAAC])
JP_BD.name_file_final = VPath(fr"premux/{JP_BD.name} (Premux).mkv")
JP_BD.a_src_cut = VPath(f"{JP_BD.name}_cut.aac")
JP_BD.do_qpfile = True


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
        runner.do_cleanup()


if __name__ == '__main__':
    filtered = chain.filterchain(JP_BD.clip_cut)
    Encoding(JP_BD, filtered).run()
elif __name__ == '__vapoursynth__':
    filtered = chain.filterchain(JP_BD.clip_cut)
    if not isinstance(filtered, vs.VideoNode):
        raise RuntimeError("Multiple output nodes were set when `vspipe` only expected one")
    else:
        filtered.set_output(0)
else:
    JP_BD.clip_cut.set_output(0)
    FILTERED = chain.filterchain(JP_BD.clip_cut)
    if not isinstance(FILTERED, vs.VideoNode):
        for i, clip_filtered in enumerate(FILTERED, start=1):  # type: ignore
            clip_filtered.set_output(i)
    else:
        FILTERED.set_output(1)
