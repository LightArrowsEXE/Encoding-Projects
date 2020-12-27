#!/usr/bin/env python3
import glob
import ntpath
import os

import lvsfunc as lvf
from acsuite import eztrim

path = glob.glob(f'{ntpath.basename(__file__)[13:-3]}/*.mkv')[0]
src = lvf.src(path)

if __name__ == "__main__":
    eztrim(src, (289, 0), path,
           f"{ntpath.basename(__file__)[13:-3]}/{ntpath.basename(__file__)[3:-3]}_cut.mka", ffmpeg_path='')
