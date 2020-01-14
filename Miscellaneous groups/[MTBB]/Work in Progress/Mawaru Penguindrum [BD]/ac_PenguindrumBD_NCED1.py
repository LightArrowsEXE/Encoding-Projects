#!/usr/bin/env python3
import acsuite
import lvsfunc as lvf
ac = acsuite.AC()


path = r'BDMV/[BDMV]輪るピングドラム/[BDMV]輪るピングドラム 2/MAWARU PENGUINDRUM 2/BDMV/STREAM/00011.m2ts'
src = lvf.src(path)

if __name__ == "__main__":
    ac.eztrim(src, [(24, -24)], path[:-4]+"wav", "PenguindrumBD_NCED1_cut.wav")
