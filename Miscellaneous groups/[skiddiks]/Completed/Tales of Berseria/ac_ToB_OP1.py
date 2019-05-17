#!/usr/bin/env python3

import vapoursynth as vs
import audiocutter
import lvsfunc as lvf
from subprocess import call


core = vs.core
ts_in = r'Zesty Fries/00006.m2ts'
src = lvf.src(ts_in)

ac = audiocutter.AudioCutter()

vid = ac.split(src, [(29921,32845)])

ac.ready_qp_and_chapters(vid)

vid.set_output(0)

if __name__ == "__main__":
    ac.cut_audio(r'ToB_OP1_cut.flac', audio_source=r'Zesty Fries/00006.flac')
