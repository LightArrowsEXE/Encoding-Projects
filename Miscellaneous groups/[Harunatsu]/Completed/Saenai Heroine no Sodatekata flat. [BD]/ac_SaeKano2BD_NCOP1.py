#!/usr/bin/env python3
import os
from acsuite import eztrim
import lvsfunc as lvf


path = r'[BDMV]冴えない彼女の育てかた♭Vol.01~Vol.06/[BDMV]冴えない彼女の育てかた♭ VOL.01/BDMV/STREAM/00009.m2ts'
src = lvf.src(path)

if __name__ == "__main__":
    eztrim(src, (24, 2184), f"{os.path.splitext(path)[0]}.wav", f"{__file__[:-3]}_cut.wav")
