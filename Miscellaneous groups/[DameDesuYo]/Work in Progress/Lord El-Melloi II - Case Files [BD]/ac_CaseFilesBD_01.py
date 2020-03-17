#!/usr/bin/env python3
import acsuite as acs
import lvsfunc as lvf
ac = acs.AC()


path = lvf.src(r'BDMV/[BDMV] Lord El-Melloi II-sei no Jikenbo ~Rail Zeppelin Grace Note~ [Vol.01]/BDROM/BDMV/STREAM/00001.m2ts')
src = lvf.src(path)

if __name__ == "__main__":
    ac.eztrim(src, [(24, -24)], path[:-4]+"wav", "CaseFilesBD_01_cut.wav")
