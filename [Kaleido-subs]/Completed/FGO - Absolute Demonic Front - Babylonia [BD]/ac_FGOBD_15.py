#!/usr/bin/env python3
import ntpath
import os

import lvsfunc as lvf
from acsuite import eztrim


path = r'BDMV/[BDMV][ANZX-15510][Fate Grand Order - Absolute Demonic Front Babylonia][Vol.4][JP]/BDROM/DISC2/BDMV/STREAM/00000.m2ts'
src = lvf.src(path)

if __name__ == "__main__":
    eztrim(src, (24, -24), path, f"{ntpath.basename(__file__)[3:-3]}_cut.mka", ffmpeg_path='')  # noqa
