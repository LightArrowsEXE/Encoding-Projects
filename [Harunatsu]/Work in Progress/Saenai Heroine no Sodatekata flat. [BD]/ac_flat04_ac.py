#!/usr/bin/env python3

import vapoursynth as vs
import audiocutter
from subprocess import call
import shutil
import os

core = vs.core
ts_in = r'[BDMV]冴えない彼女の育てかた♭Vol.01~Vol.06/[BDMV]冴えない彼女の育てかた♭ VOL.03/BDMV/STREAM/00001.m2ts'
src = core.lsmas.LWLibavSource(ts_in)

ac = audiocutter.AudioCutter()

vid = ac.split(src, [(24,32872)])

ac.ready_qp_and_chapters(vid)

vid.set_output(0)
if __name__ == "__main__":
    ac.cut_audio('flat04_audiocut.m4a', audio_source='[BDMV]冴えない彼女の育てかた♭Vol.01~Vol.06/[BDMV]冴えない彼女の育てかた♭ VOL.03/BDMV/STREAM/00001_Track01.m4a')
