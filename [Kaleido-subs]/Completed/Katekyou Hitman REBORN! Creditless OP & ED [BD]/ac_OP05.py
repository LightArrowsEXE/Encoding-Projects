#!/usr/bin/env python3

import vapoursynth as vs
import audiocutter
from subprocess import call
import shutil
import os

core = vs.core
ts_in = r"[BDMV][Katekyou Hitman REBORN!]\[家庭教師ヒットマンREBORN！][2006][TV][BDMV][Blu-ray BOX 2][JP][20170517]\REBORN2_DISC9\BDMV\STREAM\00005.m2ts"
src = core.lsmas.LWLibavSource(ts_in)

ac = audiocutter.AudioCutter()

vid = ac.split(src, [(4,2699)])

ac.ready_qp_and_chapters(vid)

vid.set_output(0)
if __name__ == "__main__":
    ac.cut_audio('OP5_cut.m4a', audio_source=r'[BDMV][Katekyou Hitman REBORN!]\[家庭教師ヒットマンREBORN！][2006][TV][BDMV][Blu-ray BOX 2][JP][20170517]\REBORN2_DISC9\BDMV\STREAM\00005_Track01.m4a')
    
