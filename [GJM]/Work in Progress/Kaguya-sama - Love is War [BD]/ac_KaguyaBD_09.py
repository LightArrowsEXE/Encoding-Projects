#!/usr/bin/env python3

import vapoursynth as vs
import audiocutter
import lvsfunc as lvf
from subprocess import call

core = vs.core
ts_in = r"BDMV/かぐや様は告らせたい Vol.5/BD/BDMV/STREAM/00001.m2ts"
src = lvf.src(ts_in)

ac = audiocutter.AudioCutter()

vid = ac.split(src, [(0,34526)])

ac.ready_qp_and_chapters(vid)

vid.set_output(0)
if __name__ == "__main__":
    ac.cut_audio(r'KaguyaBD_09_cut.m4a', audio_source=r'BDMV/かぐや様は告らせたい Vol.5/BD/BDMV/STREAM/00001.m4a')
