#!/usr/bin/env python3
import acsuite as acs
import lvsfunc as lvf
ac = acs.AC()


path = r'BDMV/[BDMV][ANZX-15501][Fate Grand Order - Absolute Demonic Front Babylonia][Vol.1][JP]/BDROM/disc2/BDMV/STREAM/00008.m2ts'
src = lvf.src(path)

if __name__ == "__main__":
    eztrim(src, (24, -28), f"{os.path.splitext(path)[0]}.wav", f"{ntpath.basename(__file__)[3:-3]}_cut.wav")
