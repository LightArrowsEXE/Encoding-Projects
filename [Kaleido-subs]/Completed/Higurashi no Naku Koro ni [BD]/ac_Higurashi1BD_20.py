#!/usr/bin/env python3
import vapoursynth as vs
import acsuite
import lvsfunc as lvf
ac = acsuite.AC()
core = vs.core


path = r'BDMV/HIGURASHI_BD/00021.m2ts'
src = lvf.src(path)
src = core.vivtc.VDecimate(src)

if __name__ == "__main__":
    ac.eztrim(src, [(0, -24)], path[:-4]+"wav", "Higurashi1BD_20_cut.wav")
