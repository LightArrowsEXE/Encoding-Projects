#!/usr/bin/env python3

import vapoursynth as vs
import audiocutter
import lvsfunc as lvf
from subprocess import call


core = vs.core
ts_in = r'G:/src/[Better-Raws] Karakai Jouzu no Takagi-san S2 - 05 (NF 1920x1080 x264 EAC3).mkv'
src = lvf.src(ts_in)

ac = audiocutter.AudioCutter()

vid = ac.split(src, [(24, src.num_frames-23)])

ac.ready_qp_and_chapters(vid)

vid.set_output(0)

if __name__ == "__main__":
    ac.cut_audio(r'Takagi05_cut.mka', audio_source=r'G:/src/[Better-Raws] Karakai Jouzu no Takagi-san S2 - 05 (NF 1920x1080 x264 EAC3).mka')
