#!/usr/bin/env python3

import vapoursynth as vs
import audiocutter
from subprocess import call
import shutil
import os
import re

core = vs.core
ts_in = r"05/The Rising of the Shield Hero E05 [1080p][AAC][JapDub][GerEngSub][Web-DL].mkv"
src = core.lsmas.LWLibavSource(ts_in)

ac = audiocutter.AudioCutter()

vid = ac.split(src, [(0,31762),(31769,34040)])

ac.ready_qp_and_chapters(vid)

vid.set_output(0)
if __name__ == "__main__":
    ac.cut_audio('05_cut.aac', audio_source='05/The Rising of the Shield Hero E05 [1080p][AAC][JapDub][GerEngSub][Web-DL]_Track02.aac')

shutil.move("05_cut.aac", "05/05_cut.aac")
