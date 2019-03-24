#!/usr/bin/env python3

import vapoursynth as vs
import audiocutter
from subprocess import call
import os

core = vs.core
ts_in = r"「ペルソナ５ ザ・ロイヤル」ティザーCM-ygyz3Mqjh0k.mkv"
src = core.lsmas.LWLibavSource(ts_in)

ac = audiocutter.AudioCutter()

vid = ac.split(src, [(30,1349)])

ac.ready_qp_and_chapters(vid)

vid.set_output(0)
if __name__ == "__main__":
    ac.cut_audio('P5RCM_cut.opus', audio_source='「ペルソナ５ ザ・ロイヤル」ティザーCM-ygyz3Mqjh0k_Track02.opus')
    
