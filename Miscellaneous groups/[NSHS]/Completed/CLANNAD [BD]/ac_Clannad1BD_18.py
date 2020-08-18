#!/usr/bin/env python3
import ntpath
import os

import lvsfunc as lvf
from acsuite import eztrim


path = r'BDMV/[KUNO-DIY][BDMV][CLANNAD][Blu-ray BOX Disc 1-5 Fin]/CLANNAD_4/BDMV/STREAM/00002.m2ts'
src = lvf.src(path)

if __name__ == "__main__":
    eztrim(src, (0, -48), f"{os.path.splitext(path)[0]}.wav", f"{ntpath.basename(__file__)[3:-3]}_cut.wav")
