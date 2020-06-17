#!/usr/bin/env python3
import os
from acsuite import eztrim
import lvsfunc as lvf


path = r'BDMV/[BDMV][191030][Kimetsu no Yaiba][Vol.4]/BDMV/STREAM/00004.m2ts'
src = lvf.src(path)

if __name__ == "__main__":
    eztrim(src, (0, 24), f"{os.path.splitext(path)[0]}.wav", f"{__file__[:-3]}_cut.wav")
