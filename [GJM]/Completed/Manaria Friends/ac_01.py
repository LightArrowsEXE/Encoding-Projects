#!/usr/bin/env python3

import vapoursynth as vs
import audiocutter
from subprocess import call
import shutil
import os

preview = 16664
part_b = 16904
endcard = 16784

core = vs.core
ts_in = r"01/Manaria01 (premux).mkv"
src = core.lsmas.LWLibavSource(ts_in)

ac = audiocutter.AudioCutter()

vid = ac.split(src, [(0,preview-1),(endcard,endcard+24),(part_b,20188),(preview,part_b)])

ac.ready_qp_and_chapters(vid)

vid.set_output(0)
if __name__ == "__main__":
    ac.cut_audio('01_cut.aac', audio_source='01/track1_jpn.aac')
    
os.remove("tmp-001.mka")
os.remove("tmp-002.mka")
os.remove("tmp-003.mka")
os.remove("tmp-004.mka")    

shutil.move("01_cut.aac", "01/01_cut.aac")
    
# NOTE FOR MANARIA:
#		Make sure to use the E-AC3 audio from danimestore Amazon, NOT the AAC from Crunchyroll
#		It's more work and not worth the effort!