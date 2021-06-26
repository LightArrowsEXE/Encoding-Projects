#!/usr/bin/env python3
import ntpath

import lvsfunc as lvf
from acsuite import eztrim

path = r"E:/src/[BDMV][アニメ]青の祓魔師/[BDMV][アニメ][111123] BlueExorcist 6/BDROM/BDMV/STREAM/00000.m2ts"
src = lvf.src(path)

if __name__ == "__main__":
    eztrim(src, (24, -25), path, f"{ntpath.basename(__file__)[3:-3]}_cut.mka", ffmpeg_path='')  # noqa
