#!/usr/bin/env python3

import vapoursynth as vs
import audiocutter
from subprocess import call

core = vs.core
ts_in = r"BDMV/[BDMV][190626][Kaguya-sama - Love Is War][Vol.4]/BDMV/STREAM/00001.m2ts"
src = core.lsmas.LWLibavSource(ts_in)

ac = audiocutter.AudioCutter()

vid = ac.split(src, [(0,34524)])

ac.ready_qp_and_chapters(vid)

vid.set_output(0)
if __name__ == "__main__":
    ac.cut_audio(r'KaguyaBD_07_cut.m4a', audio_source=r'BDMV/[BDMV][190626][Kaguya-sama - Love Is War][Vol.4]/BDMV/STREAM/00001.m4a')
