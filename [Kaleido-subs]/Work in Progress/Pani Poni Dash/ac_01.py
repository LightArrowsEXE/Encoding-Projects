#!/usr/bin/env python3

import vapoursynth as vs
import audiocutter
from subprocess import call
import shutil
import os

core = vs.core
ts_in = r"ac.mkv"
src = core.lsmas.LWLibavSource(ts_in)

ac = audiocutter.AudioCutter()

vid = ac.split(src, [(24,36465)])

ac.ready_qp_and_chapters(vid)

vid.set_output(0)
if __name__ == "__main__":
    ac.cut_audio('01_cut.m4a', audio_source=r'[BDMV][Pani Poni Dash][ぱにぽにだっしゅ！]\VOL1\BDMV\STREAM\00005.m4a')
    