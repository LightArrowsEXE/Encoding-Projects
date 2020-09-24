#!/usr/bin/env python3
import ntpath
import os

import lvsfunc as lvf
from acsuite import eztrim


path = r'11/[HorribleSubs] Kaguya-sama wa Kokurasetai S2 - 11 [1080p].mkv'
src = lvf.src(path)

if __name__ == "__main__":
    eztrim(src, (289, 0), f"{os.path.splitext(path)[0]}.mkv", f"{ntpath.basename(__file__)[3:-3]}_cut.aac", ffmpeg_path='')
