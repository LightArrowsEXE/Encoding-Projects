#!/usr/bin/env python3

import vapoursynth as vs
import audiocutter
from subprocess import call

core = vs.core
ts_in = r"../アニメ「マンガでわかる！Fate_Grand Order」-98s0s3VWwho.mkv"
src = core.lsmas.LWLibavSource(ts_in)

ac = audiocutter.AudioCutter()

vid = ac.split(src, [(0,8031)])

ac.ready_qp_and_chapters(vid)

vid.set_output(0)
if __name__ == "__main__":
    ac.cut_audio(r'FGOmanga01.mka', audio_source=r'../アニメ「マンガでわかる！Fate_Grand Order」-98s0s3VWwho.mka')
