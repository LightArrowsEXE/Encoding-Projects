#!/usr/bin/env python3
import os
from acsuite import eztrim
import lvsfunc as lvf

# Note: NCs for this show have AC3 audio, not DTS-HD!
path = r'BDMV/KIXA_90889/BDMV/STREAM/00008.m2ts'
src = lvf.src(path)

if __name__ == "__main__":
    eztrim(src, (24, -24), f"{os.path.splitext(path)[0]}.wav", f"{__file__[:-3]}_cut.wav")
