"""The encoder class. This is where the actual magic happens."""
import binascii
import os
from pathlib import Path
from typing import Any, List, Optional, Sequence, Union

import vapoursynth as vs
from lvsfunc.misc import source
from vardautomation import (JAPANESE, AudioStream, BasicTool, Chapter,
                            ChapterStream, EztrimCutter, FileInfo,
                            MatroskaXMLChapters, Mux, RunnerConfig, SelfRunner,
                            VideoStream, VPath, X264Encoder, X265Encoder,
                            make_comps)
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


def calculateCRC(f: str) -> str:
    with open(f, 'rb') as file:
        calc = file.read()
    return "%08X" % (binascii.crc32(calc) & 0xFFFFFFFF)


def appendCRC(f: Union[str, VPath]) -> None:
    from vardautomation.status import Status

    Status.info("Calculating CRC...")
    basename = str(f)
    crc = calculateCRC(basename)
    Status.info(f"CRC: {crc}")
    filename = f'{os.path.splitext(basename)[0]} [{crc}]{os.path.splitext(basename)[1]}'
    Status.info(f'Renaming {basename} -> {filename}')
    os.rename(basename, filename)


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

    def run(self, clean_up: bool = True,
            make_comp: bool = True,
            wraw: bool = False,
            ep_num: Optional[int] = None) -> None:
        """
        :param clean_up:    Perform clean-up procedure after encoding
        :param make_comp:   Create a slowpics-compatible comparison between src, flt, and enc
        """
        assert self.file.a_src
        assert self.file.a_src_cut

        v_encoder = X265Encoder('settings/x265_settings') if not wraw \
            else X264Encoder('settings/x264_settings_wraw')
        self.clip = dither_down(self.clip)

        a_extracters = [
            BasicTool(
                'eac3to',
                [self.file.path.to_str(),
                 '2:', self.file.a_src.set_track(1).to_str()]
            )
        ]

        a_cutters = [EztrimCutter(self.file, track=1)]

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

        metadata_message = 'HEVC WEBrip by LightArrowsEXE@GoodJob!Media' if not wraw \
            else 'h264 Workraw by LightArrowsEXE@GoodJob!Media'

        muxer = Mux(
            self.file,
            streams=(
                VideoStream(self.file.name_clip_output, metadata_message, JAPANESE),
                AudioStream(self.file.a_src_cut.format(1), 'AAC 2.0', JAPANESE),
                chapters if self.chapter_list else None
            )
        )

        config = RunnerConfig(v_encoder, None, a_extracters, a_cutters, None, muxer)

        runner = SelfRunner(self.clip, self.file, config)
        runner.run()

        appendCRC(self.file.name_file_final)

        if make_comp:
            try:
                generate_comparison(self.file, self.file.name_file_final.to_str(), self.clip)
            except ValueError as e:
                Status.fail(f"{e}")

        if clean_up:
            runner.do_cleanup()

        if wraw:
            mini_file = self.file
            # One of our staff has limited internet, so we need to mini-fy one wraw.
            # Also this can 100% be written way nicer, but I am too lazy and This Works:tm:
            wraw2encoder = X264Encoder('settings/x264_settings_wraw_mini')
            mini_file.name_file_final = VPath(f"wraw/Jahy_{ep_num} (mini wraw).mkv")
            mini_file.name_clip_output = VPath(mini_file.name_clip_output.to_str()[:-4] + '_mini.265')

            wraw2muxer = Mux(
                mini_file,
                streams=(
                    VideoStream(mini_file.name_clip_output, metadata_message, JAPANESE),
                    AudioStream(self.file.a_src_cut.format(1), 'AAC 2.0', JAPANESE),
                    chapters if self.chapter_list else None
                )
            )

            wraw2config = RunnerConfig(wraw2encoder, None, a_extracters, a_cutters, None, wraw2muxer)

            wraw2runner = SelfRunner(self.clip, self.file, wraw2config)
            wraw2runner.run()

            appendCRC(mini_file.name_file_final)

            if make_comp:
                try:
                    generate_comparison(self.file, self.file.name_file_final.to_str(), self.clip)
                except ValueError as e:
                    Status.fail(f"{e}")

            if clean_up:
                runner.do_cleanup()
