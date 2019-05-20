#!/usr/bin/env python3

import vapoursynth as vs
import audiocutter
from subprocess import call


core = vs.core
ts_in = r"BDMV/衛宮さんちの今日のごはん/Vol 1/BDROM/BDMV/STREAM/00002.m2ts"
src = core.lsmas.LWLibavSource(ts_in)

ac = audiocutter.AudioCutter()

vid = ac.split(src, [(24,18005)])

ac.ready_qp_and_chapters(vid)

vid.set_output(0)
if __name__ == "__main__":
    ac.cut_audio(r'02/EmiyaBD_02_cut.m4a', audio_source=r'BDMV/衛宮さんちの今日のごはん/Vol 1/BDROM/BDMV/STREAM/00002.m4a')
