#!/usr/bin/env python3

import vapoursynth as vs
import audiocutter
from subprocess import call
import shutil
import os

preview_b = 16688
endcard_b = 16808
part_b_b = 16928
epend_b = 19995

core = vs.core
ts_in = r"03/[DragsterPS] Manariafurenzu Ekusutorapaato Zuke S01E03 [1080p] [Japanese Audio] [E13CFD37].mkv"
src = core.lsmas.LWLibavSource(ts_in)

ac = audiocutter.AudioCutter()

vid = ac.split(src, [(50,preview_b-1),(endcard_b,endcard_b+48),(part_b_b,epend_b),(preview_b,part_b_b)])

ac.ready_qp_and_chapters(vid)

vid.set_output(0)
if __name__ == "__main__":
    ac.cut_audio('03_cut.aac', audio_source='03/track1_jpn.aac')
    
os.remove("tmp-001.mka")
os.remove("tmp-002.mka")
os.remove("tmp-003.mka")
os.remove("tmp-004.mka")    
        
shutil.move("03_cut.aac", "03/03_cut.aac")

# NOTE FOR MANARIA:
#		Make sure to use the E-AC3 audio from danimestore Amazon, NOT the AAC from Crunchyroll
#		It's more work and not worth the effort!