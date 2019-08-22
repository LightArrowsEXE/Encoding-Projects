#!/usr/bin/env python3

import vapoursynth as vs
import audiocutter
from subprocess import call
import shutil
import os

core = vs.core
ts_in = r'G:/Seed/ARIA SEASON ONE BD/ARIAS1BD3/BDMV/STREAM/00013.m2ts'
src = core.lsmas.LWLibavSource(ts_in)

ac = audiocutter.AudioCutter()

vid = ac.split(src, [(30,2851-90)]) # some weird audio cutting bug?

ac.ready_qp_and_chapters(vid)

vid.set_output(0)
if __name__ == "__main__":
    ac.cut_audio('ac_Aria1BD_ED1.m4a', audio_source='G:/Seed/ARIA SEASON ONE BD/ARIAS1BD3/BDMV/STREAM/00013.m4a')
