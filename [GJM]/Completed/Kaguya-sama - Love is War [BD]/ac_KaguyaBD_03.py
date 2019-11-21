#!/usr/bin/env python3
import acsuite
import lvsfunc as lvf
ac = acsuite.AC()


path = r'BDMV/かぐや様は告らせたい Vol.2/BD/BDMV/STREAM/00001.m2ts'
src = lvf.src(path)

if __name__ == "__main__":
    ac.eztrim(src, [(0, -25)], path[:-4]+"wav", "KaguyaBD_03_cut.wav")
