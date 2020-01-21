#!/usr/bin/env python3
import acsuite
import lvsfunc as lvf
ac = acsuite.AC()


path = r'BDMV/[BDMV][191204][Machikado Mazoku][Vol.3]/MACHIKADO_MAZOKU_3/BDMV/STREAM/00006.m2ts'
src = lvf.src(path)

if __name__ == "__main__":
    ac.eztrim(src, [(0, -24)], path[:-4]+"wav", "MachikadoBD_08_cut.wav")
