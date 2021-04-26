#!/usr/bin/env python3
import ntpath

import lvsfunc as lvf
from acsuite import eztrim

path = r"BDMV/[BDMV][210324][Yuru Camp Season 2][Vol.1]/BD/BDMV/STREAM/00007.m2ts"  # noqa
src = lvf.src(path)

if __name__ == "__main__":
    eztrim(src, (0, -50), path, f"{ntpath.basename(__file__)[3:-3]}_cut.mka", ffmpeg_path='')  # noqa
