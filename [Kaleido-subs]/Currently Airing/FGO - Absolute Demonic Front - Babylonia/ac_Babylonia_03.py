#!/usr/bin/env python3

import vapoursynth as vs
import audiocutter
import lvsfunc as lvf
from subprocess import call


core = vs.core
ts_in = r'03/Fate Grand Order_ Zettai Majuu Sensen Babylonia - 03 (MX).d2v'
src = lvf.src(ts_in)

if ts_in.endswith('d2v'):
    src = core.vivtc.VDecimate(src)

ac = audiocutter.AudioCutter()

vid = ac.split(src, [(809,3542),(5223,18815),(20256,37971)])

ac.ready_qp_and_chapters(vid)

vid.set_output(0)

if __name__ == "__main__":
    ac.cut_audio(r'Babylonia_03_cut.m4a', audio_source=r'03/Fate Grand Order_ Zettai Majuu Sensen Babylonia - 03 (MX) T112 stereo 244 kbps DELAY -356 ms.aac')
