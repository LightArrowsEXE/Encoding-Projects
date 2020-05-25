#!/usr/bin/env python3
import acsuite as acs
import lvsfunc as lvf
ac = acs.AC()


path = r'BDMV/JOSHIRAKU/120926_JOSHIRAKU_VOL1/BDMV/STREAM/00000.m2ts'
src = lvf.src(path)

if __name__ == "__main__":
    ac.eztrim(src, [(24, 34793)], path[:-4]+"wav", "JoshirakuBD_01_cut.wav")
