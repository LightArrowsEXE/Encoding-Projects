#!/usr/bin/env python3
import acsuite
import lvsfunc as lvf
ac = acsuite.AC()


path = r'BDMV/GRANBLUE_FANTASY_SEASON2_1/BDMV/STREAM/00008.m2ts'
src = lvf.src(path)

if __name__ == "__main__":
    ac.eztrim(src, [(0, -24)], path[:-4]+"wav", "GBF2BD_NCED1_cut.wav")
