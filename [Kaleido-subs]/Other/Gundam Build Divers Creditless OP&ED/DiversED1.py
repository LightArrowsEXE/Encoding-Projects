#!/usr/bin/env python3

import vapoursynth as vs
import audiocutter
from subprocess import call
import shutil
import os

core = vs.core
ts_in = r"F:\Convert\[BDMV][180926][Gundam Build Divers][BD-BOX1]\GUNDAM_BUILD_DIVERS_BDBOX1_D3\BDMV\STREAM\00011.m2ts"
src = core.lsmas.LWLibavSource(ts_in)

ac = audiocutter.AudioCutter()
vid = ac.split(src, [(24,2183)])

ac.ready_qp_and_chapters(vid)

vid.set_output(0)
if __name__ == "__main__":
    ac.cut_audio('track1_jpn.aac', audio_source=r'F:\Encoding\Audio\qaac_2.64\track1_jpn.aac')
       
