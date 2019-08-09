#!/usr/bin/env python3

import vapoursynth as vs
import audiocutter
import lvsfunc as lvf
from subprocess import call


core = vs.core
ts_in = r'G:/src/[Funimation] Fate Grand Order Zettai Majuu Sensen Babylonia - 00 [1080p].mkv'
src = lvf.src(ts_in)

ac = audiocutter.AudioCutter()

vid = ac.split(src, [(289, src.num_frames)])

ac.ready_qp_and_chapters(vid)

vid.set_output(0)

if __name__ == "__main__":
    ac.cut_audio(r'Babylonia00_cut.m4a', audio_source=r'G:/src/[Funimation] Fate Grand Order Zettai Majuu Sensen Babylonia - 00 [1080p]_Track02.aac')
