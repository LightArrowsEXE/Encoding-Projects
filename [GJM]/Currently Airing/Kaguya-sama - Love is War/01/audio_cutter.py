#!/usr/bin/env python3

import vapoursynth as vs
import audiocutter
from subprocess import call
import shutil
import os

core = vs.core
ts_in = r"F:\Portfolio\[Kaleido-subs]\Tate no Yuusha no Nariagari [TV]\01\[Erai-raws] Tate no Yuusha no Nariagari - 01 [1080p][Multiple Subtitle].mkv"
src = core.lsmas.LWLibavSource(ts_in)

ac = audiocutter.AudioCutter()
vid = ac.split(src, [(1318, 3474)])

ac.ready_qp_and_chapters(vid)

vid.set_output(0)
if __name__ == "__main__":
    ac.cut_audio('F:\Portfolio\[GJM]\Kaguya-sama - Love is War\01\track1_jpn_new.aac', audio_source='track1_jpn.aac')