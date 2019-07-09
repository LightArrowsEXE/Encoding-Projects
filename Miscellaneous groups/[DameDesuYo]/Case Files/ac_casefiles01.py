#!/usr/bin/env python3

import vapoursynth as vs
import audiocutter
import lvsfunc as lvf
from subprocess import call
core = vs.core


ts_in = r"01/Lord El-Melloi II-sei no Jikenbo_ Rail Zeppelin Grace Note - 01 (Wakanim SC 1080p) [!].mkv"
src = lvf.src(ts_in)

ac = audiocutter.AudioCutter()

vid = ac.split(src, [(1,15798),(15797, 15798),(15799,src.num_frames)])

ac.ready_qp_and_chapters(vid)

vid.set_output(0)
if __name__ == "__main__":
    ac.cut_audio(r'ac_casefiles01.aac', audio_source=r'01/Lord El-Melloi II-sei no Jikenbo_ Rail Zeppelin Grace Note - 01 (Wakanim SC 1080p) [!]_Track02.aac')
