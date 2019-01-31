#!/usr/bin/env python3

import vapoursynth as vs
import audiocutter
from subprocess import call
import shutil
import os

preview = 16662
part_b = 16902
edstart = 15584
endcard = 16782
epend = 20472

core = vs.core
ts_in = r"[DragsterPS] Manariafurenzu Ekusutorapaato Zuke S01E02 [1080p] [Japanese Audio] [7A8A7C74].mkv"
src = core.lsmas.LWLibavSource(ts_in)

ac = audiocutter.AudioCutter()

vid = ac.split(src, [(24,preview-1),(endcard,endcard+48),(part_b,epend),(preview,part_b)])

ac.ready_qp_and_chapters(vid)

vid.set_output(0)
if __name__ == "__main__":
    ac.cut_audio('track1_jpn_cut.mka', audio_source='track1_jpn.mka')