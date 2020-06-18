#!/usr/bin/env python3
import os
from acsuite import eztrim
import lvsfunc as lvf


path = r'BDMV/[BDMV][190402][マナリアフレンズ II]/BD/BDMV/STREAM/00012.m2ts'
src = lvf.src(path)

if __name__ == "__main__":
    eztrim(src, (1004, 1988), f"{os.path.splitext(path)[0]}.wav", f"{__file__[:-3]}_cut.wav")
