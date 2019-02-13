#!/usr/bin/env python3

import vapoursynth as vs
import audiocutter
from subprocess import call
import shutil
import os

preview_b = 16688
endcard_b = 16808
part_b_b = 16928
edstart_b = 15609
epend_b = 19995

core = vs.core
ts_in = r"03/[DragsterPS] Manariafurenzu Ekusutorapaato Zuke S01E03 [1080p] [Japanese Audio] [E13CFD37].mkv"
src = core.lsmas.LWLibavSource(ts_in)

ac = audiocutter.AudioCutter()

#src_b = src_b[26:preview_b]+blank[:48]+src_b[part_b_b:epend_b]+src_b[preview_b:part_b_b]
vid = ac.split(src, [(50,preview_b-1),(endcard_b,endcard_b+48),(part_b_b,epend_b),(preview_b,part_b_b)])

ac.ready_qp_and_chapters(vid)

vid.set_output(0)
if __name__ == "__main__":
    ac.cut_audio('03_cut.aac', audio_source='track1_jpn.aac')
    
# NOTE FOR MANARIA:
#		Make sure to use the E-AC3 audio from danimestore Amazon, NOT the AAC from Crunchyroll
#		It's more work and not worth the effort!