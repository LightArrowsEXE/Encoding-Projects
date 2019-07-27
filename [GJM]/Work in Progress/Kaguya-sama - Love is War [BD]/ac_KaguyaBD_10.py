#!/usr/bin/env python3

import vapoursynth as vs
import audiocutter
from subprocess import call

core = vs.core
ts_in = r"BDMV/かぐや様は告らせたい Vol.5/BD/BDMV/STREAM/00002.m2ts"
src = core.lsmas.LWLibavSource(ts_in).sd.AssumeFPS(fpsnum=24000, fpsden=1001)

ac = audiocutter.AudioCutter()

vid = ac.split(src, [(12,34523)])

ac.ready_qp_and_chapters(vid)

vid.set_output(0)
if __name__ == "__main__":
    ac.cut_audio(r'KaguyaBD_10_cut.m4a', audio_source=r'BDMV/かぐや様は告らせたい Vol.5/BD/BDMV/STREAM/00002.m4a')
