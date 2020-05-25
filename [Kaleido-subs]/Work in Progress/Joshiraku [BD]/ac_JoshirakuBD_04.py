#!/usr/bin/env python3
import acsuite as acs
import lvsfunc as lvf
ac = acs.AC()


path = r'BDMV/JOSHIRAKU/121024_JOSHIRAKU_VOL2/BDMV/STREAM/00000.m2ts'
src = lvf.src(path)

if __name__ == "__main__":
    ac.eztrim(src, [(34813,-46)], path[:-4]+"wav", "JoshirakuBD_04_cut.wav")
