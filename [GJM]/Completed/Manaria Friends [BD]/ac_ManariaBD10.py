#!/usr/bin/env python3

import vapoursynth as vs
import audiocutter
from subprocess import call
import os

# Note: before cutting
endcard = 16688
part_b = 16928
epend = 21002

# Note: after cutting
edstart = 13198


core = vs.core
ts_in = r"BDMV/[BDMV][190402][マナリアフレンズ II]/BD/BDMV/STREAM/00010.m2ts"
src = core.lsmas.LWLibavSource(ts_in)

ac = audiocutter.AudioCutter()

vid = ac.split(src, [(24,endcard-1),(epend-48,epend),(part_b,epend),(endcard,part_b)])

ac.ready_qp_and_chapters(vid)

vid.set_output(0)
if __name__ == "__main__":
    ac.cut_audio('ManariaBD10_ac.m4a', audio_source='BDMV/[BDMV][190402][マナリアフレンズ II]/BD/BDMV/STREAM/00011_Track01.m4a')

os.remove("tmp-001.mka")
os.remove("tmp-002.mka")
os.remove("tmp-003.mka")
os.remove("tmp-004.mka")
