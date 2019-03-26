#!/usr/bin/env python3

import vapoursynth as vs
import audiocutter
from subprocess import call
import os

endcard = 16662
part_b = 16902
epend = 20952


core = vs.core
ts_in = r"09/manaria09_video_15_decrypted.mkv"
src = core.lsmas.LWLibavSource(ts_in)

ac = audiocutter.AudioCutter()

vid = ac.split(src, [(0,endcard-1),(part_b,epend),(endcard,part_b)])

ac.ready_qp_and_chapters(vid)

vid.set_output(0)
if __name__ == "__main__":
    ac.cut_audio('10/10_cut.mka', audio_source='10/Mysteria Friends E10 [1080p][E-AC3][JapDub][GerSub][Web-DL].mka')
    
os.remove("tmp-001.mka")
os.remove("tmp-002.mka")
os.remove("tmp-003.mka")
os.remove("tmp-004.mka")

# NOTE FOR MANARIA:
#		Make sure to use the E-AC3 audio from danimestore Amazon, NOT the AAC from Crunchyroll
#		It's more work and not worth the effort!