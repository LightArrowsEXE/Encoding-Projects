from typing import List

import vapoursynth as vs
from lvsfunc.misc import replace_ranges, source
from lvsfunc.types import Range
from vardautomation import (JAPANESE, AudioCutter, AudioStream, BasicTool,
                            FileInfo, FlacEncoder, Mux, PresetBD, PresetFLAC,
                            RunnerConfig, SelfRunner, VideoStream, VPath,
                            X265Encoder)
from vsutil import insert_clip

from bento_filters import flt

core = vs.core

core.num_threads = 16

EPNUM = __file__[-5:-3]

# Sources
JPBD_NCOP1 = FileInfo(r'BDMV/Vol.1/BDMV/STREAM/00003.m2ts', 0, -24,
                      idx=lambda x: source(x, cachedir=''))
JPBD_NCOP2 = FileInfo(r'BDMV/Vol.5/BDMV/STREAM/00002.m2ts', 0, -25,
                      idx=lambda x: source(x, cachedir=''),
                      preset=[PresetBD, PresetFLAC])
JPBD_NCOP2.name_file_final = VPath(fr"premux/{JPBD_NCOP2.name} (Premux).mkv")
JPBD_NCOP2.do_qpfile = True
JPBD_NCOP2.a_src = VPath(f"{JPBD_NCOP2.name}.wav")
JPBD_NCOP2.a_src_cut = VPath(f"{JPBD_NCOP2.name}_cut.wav")
JPBD_NCOP2.a_enc_cut = VPath(f"{JPBD_NCOP2.name}_cut.flac")


# Common variables
replace_op: List[Range] = [(0, 205), (527, 597), (1350, 1575), (1613, 1673), (1735, 1933)]
op_aisle: List[Range] = [(281, 373)]
red_circle: List[Range] = [(1934, 1951), (1956, 1979), (1984, 2054)]


def main() -> vs.VideoNode:
    """Vapoursynth filtering"""
    import rekt
    from adptvgrnMod import adptvgrnMod
    from havsfunc import FastLineDarkenMOD
    from vsutil import depth

    src_NCOP1 = JPBD_NCOP1.clip_cut
    src_NCOP2 = JPBD_NCOP2.clip_cut

    src_NCOP = replace_ranges(src_NCOP2, src_NCOP1, replace_op)

    rkt = rekt.rektlvls(
        src_NCOP,
        rownum=[0, 1079], rowval=[15, 15],
        colnum=[0, 1919], colval=[15, 15]
    )
    no_rkt = replace_ranges(rkt, src_NCOP, [(0, 205)])

    scaled = flt.rescaler(no_rkt, 720)

    denoised = flt.denoiser(scaled, bm3d_sigma=[0.8, 0.6], bm3d_rad=1)

    aa_rep = flt.clamped_aa(denoised)
    trans_sraa = flt.transpose_sraa(denoised)
    aa_ranges = replace_ranges(aa_rep, trans_sraa, red_circle)

    darken = FastLineDarkenMOD(aa_ranges, strength=48, protection=6, luma_cap=255, threshold=2)

    deband = flt.masked_deband(darken, denoised=True, deband_args={'iterations': 2, 'threshold': 5.0, 'radius': 8, 'grain': 6})  # noqa
    grain = adptvgrnMod(deband, strength=0.3, luma_scaling=10, size=1.25, sharp=80, grain_chroma=False, seed=42069)

    return depth(grain, 10).std.Limiter(16 << 2, [235 << 2, 240 << 2], [0, 1, 2])


class Encoding:
    def __init__(self, file: FileInfo, clip: vs.VideoNode) -> None:
        self.file = file
        self.clip = clip

    def run(self) -> None:
        assert self.file.a_src
        assert self.file.a_enc_cut

        self.preqpfileflt()

        v_encoder = X265Encoder('x265', 'settings/x265_settings_BD_NCOP1v09')

        a_extracters = [
            BasicTool(
                'eac3to',
                [JPBD_NCOP2.path.to_str(),  # Not sure this works but we'll see
                 '2:', self.file.a_src.format(2).to_str()]
            )
        ]

        a_cutters = [AudioCutter(self.file, track=2)]
        a_encoders = [FlacEncoder(self.file, track=2)]

        muxer = Mux(
            self.file,
            streams=(
                VideoStream(self.file.name_clip_output, 'HEVC BDRip by LightArrowsEXE@Kaleido', JAPANESE),
                AudioStream(self.file.a_enc_cut.format(1), 'FLAC 2.0', JAPANESE),
                None
            )
        )

        config = RunnerConfig(v_encoder, None, a_extracters, a_cutters, a_encoders, muxer)

        runner = SelfRunner(self.clip, self.file, config)
        runner.run()
        runner.do_cleanup()

    def preqpfileflt(self) -> None:
        """Pre-QP file generation filtering so the scenes match properly"""
        self.file.clip_cut = replace_ranges(self.file.clip_cut, JPBD_NCOP2.clip_cut, replace_op)
        self.file.clip_cut = insert_clip(self.file.clip_cut, JPBD_NCOP2.clip_cut[826:1038], 823)


if __name__ == '__main__':
    filtered = main()
    filtered = filtered
    Encoding(JPBD_NCOP2, filtered).run()
else:
    JPBD_NCOP2.clip_cut.set_output(0)
    FILTERED = main()
    FILTERED.set_output(1)
