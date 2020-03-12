#!/usr/bin/env python3
import acsuite as acs
import lvsfunc as lvf
ac = acs.AC()


path = r'G:/src/PROMARE/BDMV/STREAM/00000-02.mkv'
src = lvf.src(path)

if __name__ == "__main__":
    ac.eztrim(src, [(600, -24)], path[:-4]+"_Track02.wav", "PromareBD_01_A_cut.wav")
