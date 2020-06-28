#!/usr/bin/env python3
import ntpath
import os

import lvsfunc as lvf
from acsuite import eztrim


path = r'BDMV/[BDMV][200325][Kimetsu no Yaiba][Vol.9]/BDMV/STREAM/00004.m2ts'
src = lvf.src(path)

if __name__ == "__main__":
    eztrim(src, (0, -26), f"{os.path.splitext(path)[0]}.wav", f"{ntpath.basename(__file__)[3:-3]}_cut.wav")
