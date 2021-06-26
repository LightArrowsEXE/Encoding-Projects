#!/usr/bin/env python3
import ntpath

import lvsfunc as lvf
from acsuite import eztrim

path = r"BDMV/00077.m2ts"
src = lvf.src(path)

if __name__ == "__main__":
    eztrim(src, (30, -30), path, f"{ntpath.basename(__file__)[3:-3]}_cut.mka", ffmpeg_path='')  # noqa
