#!/usr/bin/env python3
import acsuite as acs
import lvsfunc as lvf
ac = acs.AC()


path = r'BDMV/[BDMV][ANZX-15501][Fate Grand Order - Absolute Demonic Front Babylonia][Vol.1][JP]/BDROM/DISC2/BDMV/STREAM/00001.m2ts'
src = lvf.src(path)

if __name__ == "__main__":
    ac.eztrim(src, [(24, -24)], path[:-4]+"wav", "FGOBD_03_cut.wav")
