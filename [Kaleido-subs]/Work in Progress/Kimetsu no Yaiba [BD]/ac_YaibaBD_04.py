#!/usr/bin/env python3
import acsuite as acs
import lvsfunc as lvf
ac = acs.AC()


path = r'BDMV/[BDMV][190828][Kimetsu no Yaiba][Vol.2]/BDMV/STREAM/00005.m2ts'
src = lvf.src(path)

if __name__ == "__main__":
    ac.eztrim(src, [(0, -26)], path[:-4]+"wav", "YaibaBD_04_cut.wav")
