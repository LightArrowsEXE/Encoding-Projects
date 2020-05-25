#!/usr/bin/env python3
import acsuite as acs
import lvsfunc as lvf
ac = acs.AC()


path = r'BDMV/JOSHIRAKU/121128_JOSHIRAKU_VOL3/BDMV/STREAM/00000.m2ts'
src = lvf.src(path)

if __name__ == "__main__":
    ac.eztrim(src, [(24, 34790)], path[:-4]+"wav", "JoshirakuBD_05_cut.wav")
