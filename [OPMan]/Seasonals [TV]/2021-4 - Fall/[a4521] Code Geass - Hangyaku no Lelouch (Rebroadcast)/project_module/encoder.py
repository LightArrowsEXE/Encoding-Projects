"""The encoder class. This is where the actual magic happens."""
import os
import shutil
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import vapoursynth as vs
from lvsfunc.misc import source
from vardautomation import (JAPANESE, AudioStream, Chapter, ChapterStream,
                            EztrimCutter, FfmpegAudioExtracter, FFV1Encoder,
                            FileInfo, MatroskaXMLChapters, Mux, Patch,
                            RunnerConfig, SelfRunner, VideoStream, X265Encoder,
                            make_comps)
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
    make_comps(
        {
            'source': src.clip_cut,
            'filtered': flt,
            'encode': source(str(enc), force_lsmas=True, cachedir='')
        },
        num=int(src.clip_cut.num_frames / 500) if src.clip_cut.num_frames > 5000 else 80,
        collection_name=f'{src.name} Encode (autogenerated comp)',
        path=f'.comps/{src.name}', force_bt709=True, slowpics=True, public=False
    )


def pick_settings(f: FileInfo) -> str:

    ep = f.name[-2:]

    try:
        int(ep)
    except ValueError:
        ep = f.name[-3:]

    base = 'settings/x265_settings_BD'
    settings_file = f'{base}_{ep}'
    if not os.path.exists(settings_file):
        # Double-check, there's probably a nicer way to write out there but oh well
        ep = f.name[-7:]
        settings_file = f'{base}_{ep}'

    if not os.path.exists(settings_file):
        Status.warn(f"Couldn't find \"{settings_file}\"; falling back to default settings")
        settings_file = base
    else:
        Status.info(f"Succesfully found {settings_file}")
    return settings_file


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

    def run(self, clean_up: bool = True, make_comp: bool = True,
            zones: Optional[Dict[Tuple[int, int], Dict[str, Any]]] = None) -> None:
        """
        :param clean_up:    Perform clean-up procedure after encoding
        :param make_comp:   Create a slowpics-compatible comparison between src, flt, and enc
        """
        assert self.file.a_src

        v_encoder = X265Encoder(pick_settings(self.file), zones=zones)
        v_lossless_encoder = FFV1Encoder()
        self.clip = dither_down(self.clip)

        a_extracters = FfmpegAudioExtracter(self.file, track_in=0, track_out=0)
        a_cutters = EztrimCutter(self.file, track=1)

        if self.chapter_list:
            assert self.file.chapter
            assert self.file.trims_or_dfs

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
                VideoStream(self.file.name_clip_output, 'HEVC TVrip by LightArrowsEXE@Kaleido', JAPANESE),
                AudioStream(self.file.a_src_cut.set_track(1), 'AAC 2.0', JAPANESE),
                chapters if self.chapter_list else None
            )
        )

        config = RunnerConfig(
            v_encoder=v_encoder,
            v_lossless_encoder=v_lossless_encoder,
            a_extracters=a_extracters,
            a_cutters=a_cutters,
            a_encoders=None,
            muxer=muxer
        )

        runner = SelfRunner(self.clip, self.file, config)
        runner.run()

        if clean_up:
            runner.do_cleanup()

        if make_comp:
            try:
                generate_comparison(self.file, self.file.name_file_final.to_str(), self.clip)
            except ValueError as e:
                Status.fail(str(e))


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
