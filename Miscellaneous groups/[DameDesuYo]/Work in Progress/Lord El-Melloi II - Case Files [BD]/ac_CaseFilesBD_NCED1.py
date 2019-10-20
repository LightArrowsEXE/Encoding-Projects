#!/usr/bin/env python3

import ocsuite as ocs
import lvsfunc as lvf
oc = ocs.OC()


path = r'BDMV/[BDMV] Lord El-Melloi II-sei no Jikenbo ~Rail Zeppelin Grace Note~ [Vol.02]/BDROM/BDMV/STREAM/00005.m2ts'
src = lvf.src(path)

if __name__ == "__main__":
    oc.eztrim(src, [(24, -36)], path[:-4]+"wav", "CaseFilesBD_NCED1_cut.wav")
