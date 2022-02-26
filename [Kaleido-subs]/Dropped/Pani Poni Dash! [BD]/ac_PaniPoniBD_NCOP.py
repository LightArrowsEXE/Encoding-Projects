#!/usr/bin/env python3

import vapoursynth as vs
import audiocutter
import lvsfunc as lvf
from subprocess import call
import shutil
import os

core = vs.core
ts_in = r"BDMV/[BDMV][Pani Poni Dash][ぱにぽにだっしゅ！][BD BOX]/DISC6/BDMV/STREAM/00007.m2ts"
src = lvf.src(ts_in)

ac = audiocutter.AudioCutter()

vid = ac.split(src, [(24,2182)])

ac.ready_qp_and_chapters(vid)

vid.set_output(0)
if __name__ == "__main__":
    ac.cut_audio('PaniPoniBD_NCOP1_cut.m4a', audio_source=r'BDMV/[BDMV][Pani Poni Dash][ぱにぽにだっしゅ！][BD BOX]/DISC6/BDMV/STREAM/00007.m4a')

