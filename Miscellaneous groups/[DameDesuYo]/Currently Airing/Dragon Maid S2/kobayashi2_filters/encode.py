"""The encoder class. This is where the actual magic happens."""
from os import PathLike
from typing import Any, List, Optional, Sequence, Tuple, Union

import vapoursynth as vs
from bvsfunc.util import ap_video_source
from lvsfunc.misc import source
from vardautomation import (JAPANESE, AudioStream, FileInfo,
                            MatroskaXMLChapters, Mux, PresetAAC, PresetBD,
                            RunnerConfig, SelfRunner, VideoStream, VPath,
                            X264Encoder, make_comps)
from vsutil import depth

from .filter import masked_f3kdb, default_grain

core = vs.core


XML_TAG = 'settings/tags_aac.xml'

def dither_down(clip: vs.VideoNode) -> vs.VideoNode:
    """Output video node"""
    return depth(clip, 10).std.Limiter(16 << 2, [235 << 2, 240 << 2], [0, 1, 2])


def verify_trim(trims: Any) -> List[Optional[int]]:
    """Basically just to satisfy mypy. My trims should *always* be a tuple."""
    return list(trims) if isinstance(trims, tuple) else [None, None]


def generate_comparison(src: FileInfo, enc: Union[PathLike[str], str], flt: vs.VideoNode) -> None:
        make_comps(
        {
            'source': src.clip_cut,
            'filtered': flt,
            'encode': source(str(enc), force_lsmas=True, cachedir='')
        },
        num = int(src.clip_cut.num_frames / 500) if src.clip_cut.num_frames > 5000 else 50,
        collection_name=f'{src.name} Encode',
        path=f'.comps/{src.name}', force_bt709=True, slowpics=True, public=False
    )


class Encoder:
    """"Regular encoding class"""
    def __init__(self, file: FileInfo, clip: vs.VideoNode) -> None:
        self.file = file
        self.clip = clip

    def run(self, clean_up: bool = True, wraw: bool = False, make_comp: bool = True) -> None:
        assert self.file.a_src
        assert self.file.a_enc_cut

        settings_file = 'settings/x264_settings' if not wraw else 'settings/x264_settings_wraw'
        v_encoder = X264Encoder(settings_file)


        self.clip = dither_down(self.clip)

        audio_files = ap_video_source(self.file.path.to_str(),
                                      trimlist=verify_trim(self.file.trims_or_dfs),
                                      framerate=self.file.clip.fps,
                                      noflac=True, noaac=False, silent=False)

        audio_tracks: List[AudioStream] = []
        for track in audio_files:
            audio_tracks += [AudioStream(VPath(track), 'AAC 2.0', JAPANESE, XML_TAG)]

        muxer = Mux(
            self.file,
            streams=(
                VideoStream(self.file.name_clip_output, 'h264 WEBrip by LightArrowsEXE@DameDesuYo', JAPANESE),
                audio_tracks, None
            )
        )

        config = RunnerConfig(v_encoder, None, None, None, None, muxer)

        runner = SelfRunner(self.clip, self.file, config)
        runner.run()

        if make_comp:
            generate_comparison(self.file, self.file.name_file_final.to_str(), self.clip)

        if clean_up:
            runner.do_cleanup()
