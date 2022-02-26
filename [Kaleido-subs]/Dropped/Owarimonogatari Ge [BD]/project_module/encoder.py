"""The encoder class. This is where the actual magic happens."""
import os
import shutil
from typing import Any, Dict, List, Optional, Tuple, Union

import vapoursynth as vs
from bvsfunc.util.AudioProcessor import video_source
from lvsfunc.render import SceneChangeMode, find_scene_changes
from vardautomation import (ENGLISH, JAPANESE, AudioStream, FFV1Encoder,
                            FileInfo, Mux, Patch, RunnerConfig, SelfRunner,
                            VideoStream, VPath, X265Encoder)
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


def generate_keyframes(fileinfo: FileInfo) -> None:
    """Generating keyframes manually, just in case shit happens"""
    if not VPath(fileinfo.qpfile).is_file():
        with open(fileinfo.qpfile, 'w') as o:
            for f in find_scene_changes(fileinfo.clip_cut, SceneChangeMode.WWXD_SCXVID_UNION):
                o.write(f"{f} K\n")
    else:
        Status.warn('qpfile found, not rerunning keyframe generator')


class Encoder:
    """"Regular encoding class"""
    def __init__(self, file: FileInfo, clip: vs.VideoNode) -> None:
        self.file = file
        self.clip = clip

    def run(self, clean_up: bool = True,
            zones: Optional[Dict[Tuple[int, int], Dict[str, Any]]] = None) -> None:
        """
        :param clean_up:    Perform clean-up procedure after encoding
        :param zones:       x265 zones
        """
        assert self.file.a_src

        video_stream = VideoStream(self.file.name_clip_output, 'HEVC BDrip by LightArrowsEXE@Kaleido', ENGLISH)
        v_encoder = X265Encoder(r'settings/x265_settings', zones=zones)
        v_lossless_encoder = FFV1Encoder()
        self.clip = dither_down(self.clip)

        audio_files = video_source(self.file.path.to_str(),
                                   out_file=self.file.a_src_cut,
                                   trim_list=resolve_trims(self.file.trims_or_dfs),
                                   trims_framerate=self.file.clip.fps,
                                   flac=False, aac=True, silent=False)

        audio_tracks: List[AudioStream] = []
        for track in audio_files:
            audio_tracks += [AudioStream(VPath(track), 'AAC 2.0', JAPANESE, XML_TAG)]

        # generate_keyframes(self.file)

        muxer = Mux(self.file, streams=(video_stream, audio_tracks, None))

        config = RunnerConfig(
            v_encoder=v_encoder,
            v_lossless_encoder=v_lossless_encoder,
            a_extracters=None,
            a_cutters=None,
            a_encoders=None,
            muxer=muxer
        )

        # Running twice so it properly uses the qpfile
        runner = SelfRunner(self.clip, self.file, config)
        runner.run()

        if clean_up:
            runner.do_cleanup()


class Patcher:
    """"Simple patching class"""
    def __init__(self, file: FileInfo, clip: vs.VideoNode) -> None:
        self.file = file
        self.clip = clip

    def patch(self,
              ranges: Union[Union[int, Tuple[int, int]], List[Union[int, Tuple[int, int]]]],
              clean_up: bool = True,
              external_file: Optional[Union[os.PathLike[str], str]] = None) -> None:
        """
        :ranges:            Frame ranges that require patching. Expects as a list of tuples or integers (can be mixed).
                            Examples: [(0, 100), (400, 600)]; [50, (100, 200), 500]
        :param clean_up:    Perform clean-up procedure after patching
        :external_file:     File to patch into. This is intended for videos like NCs with only one or two changes
                            so you don't need to encode the entire thing multiple times.
                            It will copy the given file and rename it to ``FileInfo.name_file_final``.
                            If None, performs regular patching.
        """
        v_encoder = X265Encoder('settings/x265_settings')
        self.clip = dither_down(self.clip)

        if external_file:
            if os.path.exists(external_file):
                Status.info(f"Copying {external_file} to {self.file.name_file_final}")
                shutil.copy(external_file, self.file.name_file_final)
            else:
                Status.warn(f"{self.file.name_file_final} already exists; please ensure it's the correct file!")

        runner = Patch(
            clip=self.clip,
            ranges=ranges,  # type:ignore[arg-type]
            encoder=v_encoder,
            file=self.file,
        )
        runner.run()

        new = f"{self.file.name_file_final.to_str()[:-4]}_new.mkv"
        Status.info(f"Replacing {self.file.name_file_final} -> {new}")
        try:
            os.replace(new, self.file.name_file_final)
        except FileNotFoundError as e:
            Status.warn(f"Error while trying to move files: \n{e}\n")
            clean_up = False
            Status.warn('Disabling post-patch clean-up procedure')

        if clean_up:
            runner.do_cleanup()
