#!/usr/bin/env python3
import ntpath
import os

import lvsfunc as lvf
from acsuite import eztrim


path = r'09/[HorribleSubs] Kaguya-sama wa Kokurasetai S2 - 09 [1080p].mkv'
src = lvf.src(path)

if __name__ == "__main__":
    eztrim(src, (289, 0), f"{os.path.splitext(path)[0]}.aac", f"{ntpath.basename(__file__)[3:-3]}_cut.aac")
