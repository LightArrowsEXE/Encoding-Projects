#!/usr/bin/env python3
import acsuite as acs
import lvsfunc as lvf
ac = acs.AC()


path = lvf.src(r'BDMV/[BDMV][200115][Lord El-Melloi II-sei no Jikenbo][Vol.05]/BDROM/BDMV/STREAM/00000.m2ts')
src = lvf.src(path)

if __name__ == "__main__":
    ac.eztrim(src, [(24, -24)], path[:-4]+"wav", "CaseFilesBD_09_cut.wav")
