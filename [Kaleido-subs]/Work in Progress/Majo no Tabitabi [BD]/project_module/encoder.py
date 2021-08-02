"""The encoder class. This is where the actual magic happens."""
import os
import shutil
from pathlib import Path
from typing import Any, List, Optional, Sequence, Tuple, Union

import vapoursynth as vs
from bvsfunc.util.AudioProcessor import video_source
from lvsfunc.misc import source
from vardautomation import (JAPANESE, AudioStream, Chapter, ChapterStream,
                            FileInfo, MatroskaXMLChapters, Mux, Patch,
                            RunnerConfig, SelfRunner, VideoStream, VPath,
                            X265Encoder, make_comps)
from vardautomation.status import Status
from vsutil import depth

core = vs.core


XML_TAG = 'settings/tags_aac.xml'


def dither_down(clip: vs.VideoNode) -> vs.VideoNode:
    """Output video node"""
    return depth(clip, 10).std.Limiter(16 << 2, [235 << 2, 240 << 2], [0, 1, 2])


def verify_trim(trims: Any) -> List[Optional[int]]:
    """Basically just to satisfy mypy. My trims should *always* be a tuple."""
    return list(trims) if isinstance(trims, tuple) else [None, None]


def generate_comparison(src: FileInfo, enc: Union[os.PathLike[str], str], flt: vs.VideoNode) -> None:
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
    def __init__(self, file: FileInfo, clip: vs.VideoNode,
                 chapter_list: Optional[List[Chapter]] = None,
                 chapter_names: Sequence[str] = ['', ''],
                 chapter_offset: Optional[int] = None) -> None:
        self.file = file
        self.clip = clip
        self.chapter_list = chapter_list
        self.chapter_names = chapter_names
        self.chapter_offset = chapter_offset

    def run(self, clean_up: bool = True, make_comp: bool = True) -> None:
        """
        :param clean_up:    Perform clean-up procedure after encoding
        :param make_comp:   Create a slowpics-compatible comparison between src, flt, and enc
        """
        assert self.file.a_src

        v_encoder = X265Encoder('settings/x265_settings')
        self.clip = dither_down(self.clip)

        audio_files = video_source(self.file.path.to_str(),
                                   trimlist=verify_trim(self.file.trims_or_dfs),
                                   framerate=self.file.clip.fps,
                                   noflac=True, noaac=False, silent=False)

        audio_tracks: List[AudioStream] = []
        for track in audio_files:
            audio_tracks += [AudioStream(VPath(track), 'AAC 2.0', JAPANESE, XML_TAG)]

        if self.chapter_list:
            assert self.file.chapter
            assert self.file.trims_or_dfs

            Path("/chapters").mkdir(parents=True, exist_ok=True)

            if not isinstance(self.chapter_offset, int):
                self.chapter_offset = self.file.trims_or_dfs[0] * -1  # type: ignore

            chapxml = MatroskaXMLChapters(self.file.chapter)
            chapxml.create(self.chapter_list, self.file.clip.fps)
            chapxml.shift_times(self.chapter_offset, self.file.clip.fps)  # type: ignore
            chapxml.set_names(self.chapter_names)
            chapters = ChapterStream(chapxml.chapter_file, JAPANESE)

        muxer = Mux(
            self.file,
            streams=(
                VideoStream(self.file.name_clip_output, 'HEVC BDRip by LightArrowsEXE@Kaleido', JAPANESE),
                audio_tracks, chapters if self.chapter_list else None
            )
        )

        config = RunnerConfig(v_encoder, None, None, None, None, muxer)

        runner = SelfRunner(self.clip, self.file, config)
        runner.run()

        try:
            if make_comp:
                generate_comparison(self.file, self.file.name_file_final.to_str(), self.clip)
        except ValueError as e:
            Status.fail(str(e))

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
        os.replace(new, self.file.name_file_final)

        if clean_up:
            runner.do_cleanup()
