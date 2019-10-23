#!/usr/bin/env python3
import acsuite as acs
import lvsfunc as lvf
ac = acs.AC()


path = r'BDMV/[BDMV][190925][Kimetsu no Yaiba][Vol.3]/BDMV/STREAM/00005.m2ts'
src = lvf.src(path)

if __name__ == "__main__":
    ac.eztrim(src, [(0, -25)], path[:-4]+"wav", "YaibaBD_07_cut.wav")
