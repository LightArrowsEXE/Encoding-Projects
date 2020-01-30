#!/usr/bin/env python3
import acsuite
import lvsfunc as lvf
ac = acsuite.AC()


path = r'03/227 - 03 (Funimation 1080p).mkv'
src = lvf.src(path)

if __name__ == "__main__":
    ac.eztrim(src, [(289, 0)], path[:-4]+"_Track02.aac", "227_03_cut.aac")
