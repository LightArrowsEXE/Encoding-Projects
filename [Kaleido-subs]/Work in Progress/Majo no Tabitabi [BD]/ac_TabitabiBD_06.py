#!/usr/bin/env python3
import ntpath

import lvsfunc as lvf
from acsuite import eztrim

path = r"BDMV/[BDMV][アニメ][210127][MAJO_NO_TABITABI_1][Blu-Ray BOX 上]/BDMV/STREAM/00006.m2ts"
src = lvf.src(path)

if __name__ == "__main__":
    eztrim(src, (24, -24), path, f"{ntpath.basename(__file__)[3:-3]}_cut.mka", ffmpeg_path='')  # noqa