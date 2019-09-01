#!/usr/bin/env python3

import vapoursynth as vs
import audiocutter
from subprocess import call
import lvsfunc as lvf
import shutil
import os

core = vs.core
ts_in = r'src/Fate kaleid liner Prisma☆Illya_ Prisma☆Phantasm (Amazon CBR 1080p).mkv'
src = lvf.src(ts_in)

ac = audiocutter.AudioCutter()

vid = ac.split(src, [(528,src.num_frames)])

ac.ready_qp_and_chapters(vid)

vid.set_output(0)
if __name__ == "__main__":
    ac.cut_audio('IllyaPP_01_AC.m4a', audio_source='src/Fate kaleid liner Prisma☆Illya_ Prisma☆Phantasm (Amazon CBR 1080p).mka')
