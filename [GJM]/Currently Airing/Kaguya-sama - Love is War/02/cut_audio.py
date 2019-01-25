#!/usr/bin/env python3

import vapoursynth as vs
import audiocutter
from subprocess import call
import shutil
import os

core = vs.core
ts_in = r"F:\Portfolio\The Rising of the Shield Hero E01v2 [1080p][AAC][JapDub][GerSub][Web-DL].mkv"
src = core.lsmas.LWLibavSource(ts_in)

ac = audiocutter.AudioCutter()
vid = ac.split(src, [(1318,1318+2158)])

ac.ready_qp_and_chapters(vid)

vid.set_output(0)
if __name__ == "__main__":
    ac.cut_audio(r'track1_jpn_cut.aac', audio_source=r"track1_jpn.aac")