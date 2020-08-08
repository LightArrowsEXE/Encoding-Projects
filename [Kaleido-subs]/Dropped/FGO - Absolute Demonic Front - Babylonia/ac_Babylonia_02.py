#!/usr/bin/env python3

import vapoursynth as vs
import audiocutter
import lvsfunc as lvf
from subprocess import call


core = vs.core
ts_in = r'02/Fate Grand Order_ Zettai Majuu Sensen Babylonia - 02 (MX).d2v'
src = lvf.src(ts_in)

if ts_in.endswith('d2v'):
    src = core.vivtc.VDecimate(src)

ac = audiocutter.AudioCutter()

vid = ac.split(src, [(822,4897),(6576,16047),(17486,37984)])

ac.ready_qp_and_chapters(vid)

vid.set_output(0)

if __name__ == "__main__":
    ac.cut_audio(r'Babylonia_02_cut.m4a', audio_source=r'02/Fate Grand Order_ Zettai Majuu Sensen Babylonia - 02 (MX) T112 stereo 242 kbps DELAY -351 ms.aac')
