"""The encoder class. This is where the actual magic happens."""
import os
from typing import Any, Dict, List, Optional, Tuple

import vapoursynth as vs
from bvsfunc.util.AudioProcessor import video_source
from vardautomation import (JAPANESE, AudioStream, FFV1Encoder, FileInfo, Mux,
                            RunnerConfig, SelfRunner, VideoStream, VPath,
                            X265Encoder)
from vardautomation.status import Status
from vsutil import depth

core = vs.core


def dither_down(clip: vs.VideoNode) -> vs.VideoNode:
    """Output video node"""
    return depth(clip, 10).std.Limiter(16 << 2, [235 << 2, 240 << 2], [0, 1, 2])


def resolve_trims(trims: Any) -> Any:
    """Convert list[tuple] into list[list]. begna pls"""
    if all(isinstance(trim, tuple) for trim in trims):
        return [list(trim) for trim in trims]
    return trims


class Encoder:
    """"Regular encoding class"""
    def __init__(self, file: FileInfo, clip: vs.VideoNode) -> None:
        self.file = file
        self.clip = clip

    def run(self, clean_up: bool = True,
            zones: Optional[Dict[Tuple[int, int], Dict[str, Any]]] = None) -> None:
        """
        :param clean_up:    Perform clean-up procedure after encoding
        :param zones:       Zones for x265
        """
        v_encoder = X265Encoder('settings/x265_settings', zones=zones)
        v_lossless_encoder = FFV1Encoder()
        self.clip = dither_down(self.clip)

        video_track = VideoStream(self.file.name_clip_output, 'HEVC BDRip by LightArrowsEXE@Kaleido', JAPANESE)

        audio_files = video_source(self.file.path.to_str(),
                                   out_file=self.file.a_src_cut,
                                   trim_list=resolve_trims(self.file.trims_or_dfs),
                                   trims_framerate=self.file.clip.fps,
                                   frames_total=self.file.clip.num_frames,
                                   flac=True, aac=False, silent=False)

        audio_tracks: List[AudioStream] = []
        for track in audio_files:
            audio_tracks += [AudioStream(VPath(track), 'FLAC 2.0', JAPANESE)]

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
