#!/usr/bin/env python3
import ntpath

import lvsfunc as lvf
from acsuite import eztrim

path = f'BDMV/AKUDWAFTER/BDMV/STREAM/00002.m2ts'
src = lvf.src(path)

if __name__ == "__main__":
    # Twice because there's both a 2.0 and a 5.1 track
    eztrim(src, (24, -24), f"{path[:-5]}_1.wav", f"{ntpath.basename(__file__)[3:-3]}_51_cut.wav")
    eztrim(src, (24, -24), f"{path[:-5]}_2.wav", f"{ntpath.basename(__file__)[3:-3]}_20_cut.wav")
