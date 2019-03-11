#!/usr/bin/env python3

import vapoursynth as vs
import audiocutter
from subprocess import call

core = vs.core
ts_in = r"../[BDMV][Fate／Grand Order -MOONLIGHT／LOSTROOM-]/BDROM/BDMV/STREAM/00008.m2ts"
src = core.lsmas.LWLibavSource(ts_in)

ac = audiocutter.AudioCutter()

vid = ac.split(src, [(24,383)])

ac.ready_qp_and_chapters(vid)

vid.set_output(0)
if __name__ == "__main__":
    ac.cut_audio(r'CMs/SummerRace_CM1_cut.flac', audio_source=r'../[BDMV][Fate／Grand Order -MOONLIGHT／LOSTROOM-]/BDROM/BDMV/STREAM/00008.flac')
