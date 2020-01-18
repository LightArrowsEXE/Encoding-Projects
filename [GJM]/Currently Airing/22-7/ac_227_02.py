#!/usr/bin/env python3
import acsuite
import lvsfunc as lvf
ac = acsuite.AC()


path = r'02/227 - 02 (Funimation 1080p).mkv'
src = lvf.src(path)

if __name__ == "__main__":
    ac.eztrim(src, [(289, 0)], path[:-4]+"_Track02.aac", "227_02_cut.aac")
