from typing import List

import vapoursynth as vs
from lvsfunc.misc import replace_ranges, source
from lvsfunc.types import Range
from vardautomation import (FileInfo, Patch, PresetBD, PresetFLAC, VPath,
                            X265Encoder)

from bento_filters import flt

core = vs.core

core.num_threads = 16

EPNUM = __file__[-5:-3]

# Sources
JPBD_NCOP = FileInfo(r'BDMV/Vol.1/BDMV/STREAM/00003.m2ts', 0, -24,
                     idx=lambda x: source(x, cachedir=''),
                     preset=[PresetBD, PresetFLAC])
JPBD_EP = FileInfo(r'BDMV/Vol.3/BDMV/STREAM/00000.m2ts', 1606, 1606+JPBD_NCOP.clip_cut.num_frames,
                   idx=lambda x: source(x, cachedir=''),
                   preset=[PresetBD, PresetFLAC])
JPBD_NCOP.name_file_final = VPath(fr"premux/{JPBD_NCOP.name} (Premux).mkv")
JPBD_NCOP.do_qpfile = True


# Common variables
replace_op: List[Range] = [(418, 526)]
op_aisle: List[Range] = [(281, 373)]
red_circle: List[Range] = [(1934, 1951), (1956, 1979), (1984, 2054)]


def main() -> vs.VideoNode:
    """Vapoursynth filtering"""
    from adptvgrnMod import adptvgrnMod
    from havsfunc import FastLineDarkenMOD
    from vsutil import depth

    src_op = JPBD_NCOP.clip_cut
    src_ep = JPBD_EP.clip_cut
    src = replace_ranges(src_op, src_ep, replace_op)

    scaled = flt.rescaler(src, 720)

    denoised = flt.denoiser(scaled, bm3d_sigma=[0.8, 0.6], bm3d_rad=1)

    aa_rep = flt.clamped_aa(denoised)
    trans_sraa = flt.transpose_sraa(denoised)
    aa_ranges = replace_ranges(aa_rep, trans_sraa, red_circle)

    darken = FastLineDarkenMOD(aa_ranges, strength=48, protection=6, luma_cap=255, threshold=2)

    deband = flt.masked_deband(darken, denoised=True, deband_args={'iterations': 2, 'threshold': 5.0, 'radius': 8, 'grain': 6})  # noqa
    pdeband = flt.placebo_debander(darken, grain=4, deband_args={'iterations': 2, 'threshold': 8.0, 'radius': 10})
    deband = replace_ranges(deband, pdeband, op_aisle)

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

        p = Patch(
            file_to_fix=f'premux/{JPBD_NCOP.name[:-2]}01 (Premux).mkv',
            filtered_clip=filtered,
            frame_start=281,
            frame_end=527,
            encoder=X265Encoder('x265', 'settings/x265_settings_BD'),
            file=JPBD_NCOP,
            output_filename=VPath(fr"{JPBD_NCOP.name} (Premux).mkv")
        )
        p.run()
        p.do_cleanup()

    def preqpfileflt(self) -> None:
        """Pre-QP file generation filtering so the scenes match properly"""
        self.file.clip_cut = replace_ranges(self.file.clip_cut, JPBD_EP.clip_cut, replace_op)


if __name__ == '__main__':
    filtered = main()
    filtered = filtered
    Encoding(JPBD_NCOP, filtered).run()
else:
    JPBD_NCOP.clip_cut.set_output(0)
    FILTERED = main()
    FILTERED.set_output(1)
