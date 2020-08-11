#!/usr/bin/env python3

import vapoursynth as vs
import audiocutter
from subprocess import call


core = vs.core
ts_in = r"src/[BDMV][120919][Fate Zero][Blu-ray Disc BOX 2]/Fate／Zero Blu-ray Disc Box Ⅱ Disc5 +特典CD/BDROM/BDMV/STREAM/00008.m2ts"
src = core.lsmas.LWLibavSource(ts_in)

ac = audiocutter.AudioCutter()

vid = ac.split(src, [(840,2999)])

ac.ready_qp_and_chapters(vid)

vid.set_output(0)
if __name__ == "__main__":
    ac.cut_audio(r'FSNRN_2012_OP1_cut.m4a', audio_source=r'src/[BDMV][120919][Fate Zero][Blu-ray Disc BOX 2]/Fate／Zero Blu-ray Disc Box Ⅱ Disc5 +特典CD/BDROM/BDMV/STREAM/00008_track01.flac')
