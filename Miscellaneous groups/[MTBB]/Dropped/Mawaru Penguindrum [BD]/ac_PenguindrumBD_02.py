#!/usr/bin/env python3
import acsuite
import lvsfunc as lvf
ac = acsuite.AC()


path = r'BDMV/[BDMV]輪るピングドラム/[BDMV]輪るピングドラム 1/MAWARU PENGUINDRUM 1/BDMV/STREAM/00003.m2ts'
src = lvf.src(path)

if __name__ == "__main__":
    ac.eztrim(src, [(0, -24)], path[:-4]+"wav", "PenguindrumBD_02_cut.wav")
