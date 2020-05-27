#!/usr/bin/env python3
import acsuite as acs
import lvsfunc as lvf
ac = acs.AC()


path = r'06/[HorribleSubs] Kaguya-sama wa Kokurasetai S2 - 06 [1080p].mkv'
src = lvf.src(path)

if __name__ == "__main__":
    ac.eztrim(src, [(289, 0)], path[:-4]+"_Track02.aac", "Kaguya2_06_cut.aac")
