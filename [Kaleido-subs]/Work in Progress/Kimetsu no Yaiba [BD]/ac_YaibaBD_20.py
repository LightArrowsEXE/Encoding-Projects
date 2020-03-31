#!/usr/bin/env python3
import acsuite as acs
import lvsfunc as lvf
ac = acs.AC()


path = r'BDMV/[BDMV][200325][Kimetsu no Yaiba][Vol.9]/BDMV/STREAM/00004.m2ts'
src = lvf.src(path)

if __name__ == "__main__":
    ac.eztrim(src, [(0, -26)], path[:-4]+"wav", "YaibaBD_20_cut.wav")
