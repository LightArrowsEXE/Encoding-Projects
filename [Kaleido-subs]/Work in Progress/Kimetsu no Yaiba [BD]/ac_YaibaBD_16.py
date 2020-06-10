#!/usr/bin/env python3
import os
import acsuite as acs
import lvsfunc as lvf
ac = acs.AC()


path = r'BDMV/[BDMV][200129][Kimetsu no Yaiba][Vol.7]/BDMV/STREAM/00005.m2ts'
src = lvf.src(path)

if __name__ == "__main__":
    ac.eztrim(src, [(0, -24)], f"{os.path.splitext(path)[0]}.wav", f"{__file__[:-3]}_cut.wav")
