#!/usr/bin/env python3
import acsuite
import lvsfunc as lvf
ac = acsuite.AC()


path = r'BDMV/GRANBLUE_FANTASY_SEASON2_1/BDMV/STREAM/00001.m2ts'
src = lvf.src(path)

if __name__ == "__main__":
    ac.eztrim(src, [(0, -27)], path[:-4]+"wav", "GBF2BD_01_cut.wav")
