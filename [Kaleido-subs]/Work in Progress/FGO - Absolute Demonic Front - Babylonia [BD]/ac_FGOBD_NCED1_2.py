#!/usr/bin/env python3
import acsuite as acs
import lvsfunc as lvf
ac = acs.AC()


path = r'BDMV/[BDMV][ANZX-15507][Fate Grand Order - Absolute Demonic Front Babylonia][Vol.3][JP]/BDROM/DISC2/BDMV/STREAM/00007.m2ts'
src = lvf.src(path)

if __name__ == "__main__":
    ac.eztrim(src, [(24, -28)], path[:-4]+"wav", "FGOBD_NCED1_2_cut.wav")
