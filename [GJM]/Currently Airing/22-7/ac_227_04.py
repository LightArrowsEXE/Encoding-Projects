#!/usr/bin/env python3
import acsuite
import lvsfunc as lvf
ac = acsuite.AC()


path = r'04/[Erai-raws] 22-7 - 04 [1080p].mkv'
src = lvf.src(path)

if __name__ == "__main__":
    ac.eztrim(src, [(290, 0)], path[:-4]+"_Track02.aac", "227_04_cut.aac")
