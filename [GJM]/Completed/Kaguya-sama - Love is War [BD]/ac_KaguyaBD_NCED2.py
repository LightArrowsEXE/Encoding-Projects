#!/usr/bin/env python3

import vapoursynth as vs
import audiocutter
from subprocess import call

core = vs.core
ts_in = r"BDMV/かぐや様は告らせたい Vol.2/BD/BDMV/STREAM/00009.m2ts"
src = core.lsmas.LWLibavSource(ts_in)

ac = audiocutter.AudioCutter()

vid = ac.split(src, [(0,2348)])

ac.ready_qp_and_chapters(vid)

vid.set_output(0)
if __name__ == "__main__":
    ac.cut_audio(r'KaguyaBD_NCED2_cut.m4a', audio_source=r'BDMV/かぐや様は告らせたい Vol.2/BD/BDMV/STREAM/00009_Track01.m4a')
