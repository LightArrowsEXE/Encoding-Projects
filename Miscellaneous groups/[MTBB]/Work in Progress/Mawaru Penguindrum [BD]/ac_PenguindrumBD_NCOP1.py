#!/usr/bin/env python3
import acsuite
import lvsfunc as lvf
ac = acsuite.AC()


path = r'BDMV/[BDMV]輪るピングドラム/[BDMV]輪るピングドラム 2/MAWARU PENGUINDRUM 2/BDMV/STREAM/00010.m2ts'
src = lvf.src(path)

if __name__ == "__main__":
    ac.eztrim(src, [(24, -25)], path[:-4]+"wav", "PenguindrumBD_NCOP1_cut.wav")
