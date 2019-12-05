#!/usr/bin/env python3
import acsuite
import lvsfunc as lvf
ac = acsuite.AC()

# Note: NCs for this show have AC3 audio, not DTS-HD!
path = r'BDMV/KIXA_90889/BDMV/STREAM/00008.m2ts'
src = lvf.src(path)

if __name__ == "__main__":
    ac.eztrim(src, [(24, -24)], path[:-4]+"flac", "SymphoXVBD_NCED1_cut.flac")
