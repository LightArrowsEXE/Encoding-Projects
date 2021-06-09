#!/usr/bin/env python3
import glob
import itertools as it
import ntpath

import lvsfunc as lvf
from acsuite import eztrim


path = glob.glob(f'{ntpath.basename(__file__)[-5:-3]}/*.mkv')[1]
src = lvf.src(path)

if __name__ == "__main__":
    eztrim(src, (168, 0), path, f"{ntpath.basename(__file__)[3:-3]}_cut.mka", ffmpeg_path='')  # noqa
