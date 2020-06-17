#!/usr/bin/env python3
import os
from acsuite import eztrim
import lvsfunc as lvf


path = r'BDMV/Fate Extra Last Encore/Vol6/BDROM/BDMV/STREAM/00001.m2ts'
src = lvf.src(path)

if __name__ == "__main__":
    eztrim(src, (24, -24), f"{os.path.splitext(path)[0]}.wav", f"{__file__[3:-3]}_cut.wav")
