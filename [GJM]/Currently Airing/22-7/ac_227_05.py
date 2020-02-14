#!/usr/bin/env python3
import acsuite
import lvsfunc as lvf
ac = acsuite.AC()


path = r'05/[Erai-raws] 22-7 - 05 [1080p].mkv'
src = lvf.src(path)

if __name__ == "__main__":
    ac.eztrim(src, [(289, 0)], path[:-4]+"_Track02.aac", "227_05_cut.aac")
