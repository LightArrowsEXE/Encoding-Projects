from typing import List

import vapoursynth as vs
from lvsfunc.misc import source
from lvsfunc.types import Range
from vardautomation import (JAPANESE, AudioCutter, AudioStream, BasicTool,
                            FileInfo, FlacEncoder, Mux, PresetBD, PresetFLAC,
                            RunnerConfig, SelfRunner, VideoStream, VPath,
                            X265Encoder)

from bento_filters import flt

core = vs.core

core.num_threads = 16

EPNUM = __file__[-5:-3]


# Sources
JPBD = FileInfo(r'BDMV/Vol.2/BDMV/STREAM/00003.m2ts', 0, -24,
                idx=lambda x: source(x, cachedir=''),
                preset=[PresetBD, PresetFLAC])
JPBD.name_file_final = VPath(fr"premux/{JPBD.name} (Premux).mkv")
JPBD.do_qpfile = True
JPBD.a_src = VPath(f"{JPBD.name}.wav")
JPBD.a_src_cut = VPath(f"{JPBD.name}_cut.wav")
JPBD.a_enc_cut = VPath(f"{JPBD.name}_cut.flac")

# Common variables
fucky_lineart: List[Range] = [(981, 986), (999, 1004)]
strong_deband: List[Range] = [(0, 27), (210, 309), (1350, 1529)]
zoning: List[Range] = [(109, 180), (1024, 1065), (1088, 1224)]


def main() -> vs.VideoNode:
    """Vapoursynth filtering"""
    from adptvgrnMod import adptvgrnMod
    from havsfunc import FastLineDarkenMOD
    from lvsfunc.misc import replace_ranges
    from vardefunc.noise import decsiz
    from vsutil import depth

    src = JPBD.clip_cut

    scaled = flt.rescaler(src, 720)

    denoised = flt.denoiser(scaled, bm3d_sigma=[0.8, 0.6], bm3d_rad=1)

    aa_rep = flt.clamped_aa(denoised)
    trans_sraa = flt.transpose_sraa(denoised)
    aa_sf = replace_ranges(aa_rep, trans_sraa, fucky_lineart)

    darken = FastLineDarkenMOD(aa_sf, strength=48, protection=6, luma_cap=255, threshold=2)

    deband = flt.masked_deband(darken, denoised=True, deband_args={'iterations': 2, 'threshold': 5.0, 'radius': 8, 'grain': 6})  # noqa  # noqa
    pdeband = flt.placebo_debander(darken, grain=4, deband_args={'iterations': 2, 'threshold': 8.0, 'radius': 10})
    deband = replace_ranges(deband, pdeband, strong_deband)

    grain = adptvgrnMod(deband, strength=0.3, luma_scaling=10, size=1.25, sharp=80, grain_chroma=False, seed=42069)

    # Filtering these arcade scenes is too destructive. Most we're doing here is minor filesavings
    decs_only = decsiz(depth(src, 16), sigmaS=8.0, min_in=208 << 8, max_in=240 << 8)
    no_flt = replace_ranges(grain, decs_only, zoning)

    return depth(no_flt, 10).std.Limiter(16 << 2, [235 << 2, 240 << 2], [0, 1, 2])


class Encoding:
    def __init__(self, file: FileInfo, clip: vs.VideoNode) -> None:
        self.file = file
        self.clip = clip

    def run(self) -> None:
        assert self.file.a_src
        assert self.file.a_enc_cut

        v_encoder = X265Encoder('x265', 'settings/x265_settings_BD_Ep4NC')

        a_extracters = [
            BasicTool(
                'eac3to',
                [self.file.path.to_str(),
                 '2:', self.file.a_src.format(1).to_str()]
            )
        ]

        a_cutters = [AudioCutter(self.file, track=1)]
        a_encoders = [FlacEncoder(self.file, track=1)]

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


if __name__ == '__main__':
    print
    filtered = main()
    filtered = filtered
    Encoding(JPBD, filtered).run()
else:
    JPBD.clip_cut.set_output(0)
    FILTERED = main()
    FILTERED.set_output(1)
