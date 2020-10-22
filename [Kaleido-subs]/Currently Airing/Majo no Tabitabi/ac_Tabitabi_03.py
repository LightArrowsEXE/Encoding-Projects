#!/usr/bin/env python3
import ntpath
import os

import lvsfunc as lvf
from acsuite import eztrim


ep = "03"  # The only annoying thing about using SubsPlease over Erai now is the CRC
path = f'{ep}/[SubsPlease] Majo no Tabitabi - {ep} (1080p) [6BDDDE8D].mkv'
src = lvf.src(path)

if __name__ == "__main__":
    eztrim(src, (240, 0), path,
           f"{ep}/{ntpath.basename(__file__)[3:-3]}_cut.mka", ffmpeg_path='')
