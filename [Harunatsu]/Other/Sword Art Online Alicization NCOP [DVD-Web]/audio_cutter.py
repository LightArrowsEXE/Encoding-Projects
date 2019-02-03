#!/usr/bin/env python3

import vapoursynth as vs
import audiocutter
from subprocess import call
import lvsfunc as lvf
import shutil
import os

core = vs.core
ts_in = r"VTS_01_1.VOB.d2v"
src = lvf.src(ts_in)

ac = audiocutter.AudioCutter()

vid = ac.split(src, [(6990,9689)])

ac.ready_qp_and_chapters(vid)

vid.set_output(0)
if __name__ == "__main__":
    ac.cut_audio('track1_jpn_cut.aac', audio_source='track1_jpn.m4a')
   