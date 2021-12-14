"""The encoder class. This is where the actual magic happens."""
import os
from typing import Any, List, Union

import vapoursynth as vs
from bvsfunc.util.AudioProcessor import video_source
from lvsfunc.misc import source
from vardautomation import (JAPANESE, AudioStream, FFV1Encoder, FileInfo, Mux,
                            RunnerConfig, SelfRunner, VideoStream, VPath,
                            X265Encoder, make_comps)
from vardautomation.status import Status
from vsutil import depth

core = vs.core


XML_TAG = 'settings/tags_aac.xml'


def dither_down(clip: vs.VideoNode) -> vs.VideoNode:
    """Output video node"""
    return depth(clip, 10).std.Limiter(16 << 2, [235 << 2, 240 << 2], [0, 1, 2])


def resolve_trims(trims: Any) -> Any:
    """Convert list[tuple] into list[list]. begna pls"""
    if all(isinstance(trim, tuple) for trim in trims):
        return [list(trim) for trim in trims]
    return trims


def generate_comparison(src: FileInfo, enc: Union[os.PathLike[str], str], flt: vs.VideoNode) -> None:
    """Generates a comparison and uploads it to slowpics"""
    make_comps(
        {
            'source': src.clip_cut,
            'filtered': flt,
            'encode': source(str(enc), force_lsmas=True, cachedir='')
        },
        num=int(src.clip_cut.num_frames / 500) if src.clip_cut.num_frames > 5000 else 50,
        collection_name=f'[Kaleido-subs] {src.name} Encode test',
        path=f'.comps/{src.name}', force_bt709=True, slowpics=True, public=False
    )


class Encoder:
    """"Regular encoding class"""
    def __init__(self, file: FileInfo, clip: vs.VideoNode) -> None:
        """
        :param file:                FileInfo object to use for encoding info
        :param clip:                Filtered vs.VideoNode
        """
        self.file = file
        self.clip = clip

    def run(self, clean_up: bool = True, make_comp: bool = True) -> None:
        """
        :param clean_up:    Perform clean-up procedure after encoding
        :param make_comp:   Create a slowpics-compatible comparison between src, flt, and enc
        """
        v_encoder = X265Encoder('settings/x265_settings_BD')
        v_lossless_encoder = FFV1Encoder()
        self.clip = dither_down(self.clip)

        video_track = VideoStream(self.file.name_clip_output, 'HEVC BDRip by LightArrowsEXE@Kaleido', JAPANESE)

        audio_files = video_source(self.file.path.to_str(),
                                   out_file=self.file.a_src_cut,
                                   trim_list=resolve_trims(self.file.trims_or_dfs),
                                   trims_framerate=self.file.clip.fps,
                                   frames_total=self.file.clip.num_frames,
                                   flac=False, aac=True, silent=False)

        audio_tracks: List[AudioStream] = []
        for track in audio_files:
            audio_tracks += [AudioStream(VPath(track), 'AAC 2.0', JAPANESE, XML_TAG)]

        muxer = Mux(
            self.file,
            streams=(
                video_track,
                audio_tracks,
                None
            )
        )

        config = RunnerConfig(
            v_encoder=v_encoder,
            v_lossless_encoder=v_lossless_encoder,
            a_extracters=None,
            a_cutters=None,
            a_encoders=None,
            muxer=muxer
        )

        runner = SelfRunner(self.clip, self.file, config)
        runner.run()

        if clean_up:
            runner.do_cleanup()
            for at in audio_files:
                try:
                    os.remove(at)
                except FileNotFoundError:
                    Status.warn(f"File {at} not found! Skipping...")

        if make_comp:
            try:
                generate_comparison(self.file, self.file.name_file_final.to_str(), self.clip)
            except ValueError as e:
                print(e)
