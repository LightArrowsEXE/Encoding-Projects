#!/usr/bin/env python3
import ntpath
import os

import lvsfunc as lvf
from acsuite import eztrim


path = r'BDMV/[BDMV][200429][Kimetsu no Yaiba][Vol.10]/BDMV/STREAM/00008.m2ts'
src = lvf.src(path)

if __name__ == "__main__":
    eztrim(src, (0, -24), f"{os.path.splitext(path)[0]}.wav", f"{ntpath.basename(__file__)[3:-3]}_cut.wav")
