#!/usr/bin/env python3
import acsuite as acs
import lvsfunc as lvf
ac = acs.AC()


path = r'BDMV/[BDMV] Lord El-Melloi II-sei no Jikenbo ~Rail Zeppelin Grace Note~ [Vol.02]/BDROM/BDMV/STREAM/00005.m2ts'
src = lvf.src(path)

if __name__ == "__main__":
    ac.eztrim(src, [(24, -38)], path[:-4]+"wav", "CaseFilesBD_NCED1_cut.wav")
