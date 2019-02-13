#!/usr/bin/env python3

import vapoursynth as vs
import audiocutter
from subprocess import call
import shutil
import os

preview = 16662
endcard = 16782
part_b = 16902
epend = 20185


core = vs.core
ts_in = r"04/[DragsterPS] Manariafurenzu Ekusutorapaato Zuke S01E03 [1080p] [Japanese Audio] [E13CFD37].mkv"
src = core.lsmas.LWLibavSource(ts_in)

ac = audiocutter.AudioCutter()

vid = ac.split(src, [(0,preview-1),(endcard,endcard+48),(part_b,epend),(preview,part_b)])

ac.ready_qp_and_chapters(vid)

vid.set_output(0)
if __name__ == "__main__":
    ac.cut_audio('track1_jpn_cut.aac', audio_source='track1_jpn.aac')
    
# NOTE FOR MANARIA:
#		Make sure to use the E-AC3 audio from danimestore Amazon, NOT the AAC from Crunchyroll
#		It's more work and not worth the effort!