#!/usr/bin/env python3
import ntpath
import os

import lvsfunc as lvf
from acsuite import eztrim


path = r'BDMV/[BDMV][200624][Fate Grand Order Zettai Majuu Sensen Babylonia][Vol.05]/DISC2/BDROM/BDMV/STREAM/00000.m2ts'
src = lvf.src(path)

if __name__ == "__main__":
    eztrim(src, (24, -24), f"{os.path.splitext(path)[0]}.wav", f"{ntpath.basename(__file__)[3:-3]}_cut.wav")
