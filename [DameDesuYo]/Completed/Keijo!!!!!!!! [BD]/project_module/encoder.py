"""The encoder class. This is where the actual magic happens."""
from __future__ import annotations

import collections
import os
import shutil
from glob import glob
from typing import Any, Dict, List, Sequence, Tuple

import __main__
import vapoursynth as vs
from bvsfunc.util.AudioProcessor import video_source
from lvsfunc.misc import source
from vardautomation import (FFV1, JAPANESE, X264, X265, AudioStream, Chapter,
                            ChapterStream, FileInfo, MatroskaXMLChapters, Mux,
                            Patch, RunnerConfig, SelfRunner, VideoStream,
                            VPath, logger, make_comps)
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


def parse_name(config: Dict[str, Any], file_name: str) -> VPath:
    """Converts a string to a proper path based on what's in the config file and __file__ name."""
    file_name = os.path.basename(file_name).split("_")
    file_name[-1] = os.path.splitext(file_name[-1])[0]

    output_name = config['output_name']
    output_dir = config['output_dir']
    show_name = config['show_name']

    if show_name:
        file_name[0] = show_name

    output_name = output_name.replace('$$', file_name[0]).replace('%%', file_name[-1])

    if '&&' in output_name:
        version: int = len(glob(f"{output_dir}/*{file_name[-1]}*.*", recursive=False)) + 1
        output_name = output_name.replace('&&', f"v{version}")

    return VPath(output_dir + '/' + os.path.basename(output_name) + '.mkv')


def generate_comparison(src: FileInfo, enc: os.PathLike[str] | str, flt: vs.VideoNode,
                        num: int | None = None, **kwargs: Any) -> None:
    from datetime import datetime

    if not num:
        num = int(src.clip_cut.num_frames / 500) if src.clip_cut.num_frames > 5000 else 70

    make_comps(
        {
            'source': src.clip_cut,
            'filtered': flt,
            'encode': source(str(enc), force_lsmas=True, cachedir='')
        },
        num=num,
        path=f'.comps/{src.name}_{datetime.now().strftime("%d_%m_%Y-%H_%M_%S")}',
        force_bt709=True, **kwargs
    )


class Encoder:
    """"Regular encoding class"""
    def __init__(self, file: FileInfo, clip: vs.VideoNode,
                 chapter_list: List[Chapter] | None = None,
                 chapter_names: Sequence[str] | None = None,
                 chapter_offset: int | None = None) -> None:
        self.file = file
        self.clip = clip
        self.chapter_list = chapter_list
        self.chapter_names = chapter_names
        self.chapter_offset = chapter_offset

    def run(self, clean_up: bool = True, lossless: bool = False, make_comp: bool = False,
            x264: bool = False, prefetch: int | None = None, flac: bool = False, all_tracks: bool = False,
            zones: Dict[Tuple[int, int], Dict[str, Any]] | None = None,
            qp_clip: vs.VideoNode | None = None, audio_clip: FileInfo | None = None,
            audio_file: str | None = None,
            resumable: bool = True, settings: str | None = None) -> None:
        """
        :param clean_up:    Perform clean-up procedure after encoding
        :param lossless:    Create a lossless intermediary encode
        :param make_comp:   Create a slowpics-compatible comparison between src, flt, and enc

        :param x264:        Encode using x264. If False, encode using x265 instead
        :param prefetch:    Prefetch frames. Set a low value to limit the amount of VS frames rendered at once
        :param flac:        Encode the audio to FLAC. If False, encode to AAC instead
        :param all_tracks:  Include commentary/alt tracks if there are any in the source file

        :param zones:       Zones for x264/x265
        :param qp_clip:     Optional qp clip for the qpfile creation. Useful for DVD encodes
        :param audio_clip:  Optional audio clip for the audio extracting. Useful for DVD/VFR encodes.
                            Must be FileInfo object.
        :param audio_file:  Custom audio file. Must be a string. Useful for DVD encodes.
                            If None, sets it to audio clip's audio path.
        :param resumable:   Enable resumable encoding
        :param settings:    Pass custom settings file. Else use default `settings/x26X_settings` file
        """
        assert self.file.a_src

        if zones:
            zones = collections.OrderedDict(sorted(zones.items()))

        # Video encoder
        logger.info(f'Encoding using {"x264" if x264 else "x265"}. Zones set: '
                    + f'\n{str(zones)}' if zones is not None else 'None')

        if settings is None:
            settings = 'settings/x264_settings' if x264 else 'settings/x265_settings'

        v_encoder = X264(settings, zones=zones) if x264 else X265(settings, zones=zones)

        if prefetch:
            v_encoder.prefetch = prefetch

        if resumable:
            v_encoder.resumable = True

        qp_clip = self.file.clip_cut if not qp_clip else qp_clip

        # Lossless mode
        logger.info(f'Lossless mode: {lossless}')
        v_lossless_encoder = FFV1() if lossless else None
        self.clip = dither_down(self.clip)

        # Audio encoding
        logger.info(f'Audio codec: {"AAC" if flac is False else "FLAC"}')

        if any([audio_clip, audio_file]):
            audio_file = audio_file or audio_clip.path.to_str()

        audio_files = video_source(
            in_file=self.file.path.to_str() if not audio_file else audio_file,
            out_file=self.file.a_src_cut,
            trim_list=resolve_trims(self.file.trims_or_dfs if not audio_clip else audio_clip.trims_or_dfs),
            trims_framerate=self.file.clip.fps if not audio_clip else audio_clip.clip.fps,
            frames_total=self.file.clip.num_frames if not audio_clip else audio_clip.clip.num_frames,
            flac=flac, aac=flac is False, silent=False)

        XML_TAG = 'settings/tags_aac.xml'

        audio_tracks: List[AudioStream] = []
        for track in audio_files:
            audio_tracks += [AudioStream(VPath(track), 'FLAC 2.0' if flac else 'AAC 2.0',
                                         JAPANESE, XML_TAG if not flac else None)]

        if len(audio_tracks) > 1 and not all_tracks:
            logger.warning(f'{len(audio_tracks)} audio tracks found! Only the first track will be included!')
            audio_tracks = audio_tracks[0]

        # Chapters
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

        # Muxing
        muxer = Mux(
            self.file,
            streams=(
                VideoStream(self.file.name_clip_output, 'Original encode by LightArrowsEXE@Kaleido', JAPANESE),
                audio_tracks, chapters if self.chapter_list else None
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
        runner.inject_qpfile_params(qpfile_clip=qp_clip)
        runner.run()

        if clean_up:
            runner.work_files.clear()
            for at in audio_files:
                try:
                    os.remove(at)
                except FileNotFoundError:
                    logger.warning(f"File {at} not found! Skipping")

        if make_comp:
            try:
                generate_comparison(self.file, self.file.name_file_final.to_str(), self.clip)
            except ValueError as e:
                logger.warning(str(e))


class Patcher:
    """"Simple patching class"""
    def __init__(self, file: FileInfo, clip: vs.VideoNode) -> None:
        self.file = file
        self.clip = clip

    def patch(self,
              ranges: int | Tuple[int, int] | List[int | Tuple[int, int]],
              clean_up: bool = True,
              external_file: os.PathLike[str] | str | None = None) -> None:
        """
        :ranges:            Frame ranges that require patching. Expects as a list of tuples or integers (can be mixed).
                            Examples: [(0, 100), (400, 600)]; [50, (100, 200), 500]
        :param clean_up:    Perform clean-up procedure after patching
        :external_file:     File to patch into. This is intended for videos like NCs with only one or two changes
                            so you don't need to encode the entire thing multiple times.
                            It will copy the given file and rename it to ``FileInfo.name_file_final``.
                            If None, performs regular patching.
        """
        v_encoder = X265('settings/x265_settings')
        self.clip = dither_down(self.clip)

        if external_file:
            if os.path.exists(external_file):
                logger.info(f"Copying {external_file} to {self.file.name_file_final}")
                shutil.copy(external_file, self.file.name_file_final)
            else:
                logger.warning(f"{self.file.name_file_final} already exists; please ensure it's the correct file!")

        runner = Patch(
            clip=self.clip,
            ranges=ranges,  # type:ignore[arg-type]
            encoder=v_encoder,
            file=self.file,
        )
        runner.run()

        new = f"{self.file.name_file_final.to_str()[:-4]}_new.mkv"
        logger.info(f"Replacing {self.file.name_file_final} -> {new}")
        os.replace(new, self.file.name_file_final)

        if clean_up:
            runner.do_cleanup()
