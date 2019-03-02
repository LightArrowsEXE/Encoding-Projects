#!/usr/bin/env python3

import vapoursynth as vs
import audiocutter
from subprocess import call
import shutil
import os

core = vs.core
ts_in = r'Zoku_Owarimonogatari/BDMV/STREAM/00001.m2ts'
src = core.lsmas.LWLibavSource(ts_in)

ac = audiocutter.AudioCutter()

vid = ac.split(src, [(24,35388)])

ac.ready_qp_and_chapters(vid)

vid.set_output(0)
if __name__ == "__main__":
    ac.cut_audio('ZokuOwari01_audiocut.m4a', audio_source='Zoku_Owarimonogatari/BDMV/STREAM/00001_Track01.m4a')
