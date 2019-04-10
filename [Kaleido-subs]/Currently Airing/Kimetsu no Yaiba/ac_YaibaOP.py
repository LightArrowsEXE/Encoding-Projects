#!/usr/bin/env python3

import vapoursynth as vs
import audiocutter
from subprocess import call

core = vs.core
ts_in = r"01/Demon Slayer Kimetsu no Yaiba E01 [1080p][AAC][JapDub][GerSub][Web-DL].mp4"
src = core.lsmas.LWLibavSource(ts_in)

ac = audiocutter.AudioCutter()

vid = ac.split(src, [(30449,32605)])

ac.ready_qp_and_chapters(vid)

vid.set_output(0)
if __name__ == "__main__":
    ac.cut_audio(r'01/Yaiba01_cut.mka', audio_source=r'01/Demon Slayer Kimetsu no Yaiba E01 [1080p][AAC][JapDub][GerSub][Web-DL].mka')
