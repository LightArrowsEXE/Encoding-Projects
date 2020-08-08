#!/usr/bin/env python3

import vapoursynth as vs
import audiocutter
import lvsfunc as lvf
from subprocess import call


core = vs.core
ts_in = r'01/Fate Grand Order_ Zettai Majuu Sensen Babylonia - 01 (MX).d2v'
src = lvf.src(ts_in)

if ts_in.endswith('d2v'):
    src = core.vivtc.VDecimate(src)

ac = audiocutter.AudioCutter()

vid = ac.split(src, [(844,3519),(5199,19343),(20783,37971-31)])

ac.ready_qp_and_chapters(vid)

vid.set_output(0)

if __name__ == "__main__":
    ac.cut_audio(r'Babylonia_01_cut.m4a', audio_source=r'01/Fate Grand Order_ Zettai Majuu Sensen Babylonia - 01 (MX) T112 stereo 255 kbps DELAY -310 ms.aac')
