#!/usr/bin/env python3

import vapoursynth as vs
import audiocutter
import lvsfunc as lvf
from subprocess import call


core = vs.core
ts_in = r'02/Val x Love - 02 (AT-X HD MPEG2).d2v'
src = lvf.src(ts_in)

if ts_in.endswith('d2v'):
    src = core.vivtc.VDecimate(src)

ac = audiocutter.AudioCutter()

vid = ac.split(src, [(739,3687),(3928,35027)])

ac.ready_qp_and_chapters(vid)

vid.set_output(0)

if __name__ == "__main__":
    ac.cut_audio(r'ValxLove_02_cut.m4a', audio_source=r'02/Val x Love - 02 (AT-X HD MPEG2) T104f stereo 255 kbps DELAY -322 ms.aac')
