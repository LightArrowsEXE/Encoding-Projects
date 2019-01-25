#!/usr/bin/env python3

import vapoursynth as vs
import audiocutter
from subprocess import call
import shutil
import os

preview = 16664
part_b = 16904
edstart = 15586
endcard = 16784

core = vs.core
ts_in = r"Manaria01 (premux).mkv"
src = core.lsmas.LWLibavSource(ts_in)

ac = audiocutter.AudioCutter()

vid = ac.split(src, [(0,preview-1),(endcard,endcard+24),(part_b,20188),(preview,part_b)])

ac.ready_qp_and_chapters(vid)

vid.set_output(0)
if __name__ == "__main__":
    ac.cut_audio('track1_jpn_cut.aac', audio_source='track1_jpn.aac')