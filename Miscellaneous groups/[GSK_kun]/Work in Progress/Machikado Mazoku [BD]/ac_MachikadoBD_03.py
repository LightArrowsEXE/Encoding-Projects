#!/usr/bin/env python3
import acsuite
import lvsfunc as lvf
ac = acsuite.AC()


path = r'BDMV/[BDMV][191002][Machikado Mazoku][Vol.1]/MACHIKADO_MAZOKU_1/BDMV/STREAM/00007.m2ts'
src = lvf.src(path)

if __name__ == "__main__":
    ac.eztrim(src, [(0, -24)], path[:-4]+"wav", "MachikadoBD_03_cut.wav")
