#!/usr/bin/env python3

import vapoursynth as vs
import audiocutter
from subprocess import call
import os

core = vs.core
ts_in = r"../Fate Grand Order -First Order-/BDROM/BDMV/STREAM/00000.m2ts"
src = core.lsmas.LWLibavSource(ts_in)

ac = audiocutter.AudioCutter()

vid = ac.split(src, [(24,103912)])

ac.ready_qp_and_chapters(vid)

vid.set_output(0)
if __name__ == "__main__":
    ac.cut_audio('FGO_FO01_cut.aac', audio_source='../Fate Grand Order -First Order-/BDROM/BDMV/STREAM/00000.flac')
    
