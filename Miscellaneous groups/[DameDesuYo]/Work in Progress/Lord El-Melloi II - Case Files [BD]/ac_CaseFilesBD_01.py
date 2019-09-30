#!/usr/bin/env python3

import vapoursynth as vs
import audiocutter
import lvsfunc as lvf
from subprocess import call


core = vs.core
ts_in = r'G:\src\[BDMV] Lord El-Melloi II Sei no Jikenbo\Vol 1\BDROM\BDMV\STREAM\00001.m2ts'
src = lvf.src(ts_in)

ac = audiocutter.AudioCutter()

vid = ac.split(src, [(24, src.num_frames-24)])

ac.ready_qp_and_chapters(vid)

vid.set_output(0)

if __name__ == "__main__":
    ac.cut_audio(r'CaseFilesBD_01_cut.m4a', audio_source=r'G:\src\[BDMV] Lord El-Melloi II Sei no Jikenbo\Vol 1\BDROM\BDMV\STREAM\00001.m4a')