#!/usr/bin/env python3
import acsuite as acs
import lvsfunc as lvf
ac = acs.AC()


path = r'01/[HorribleSubs] Kaguya-sama wa Kokurasetai S2 - 01 [1080p].mkv'
src = lvf.src(path)

if __name__ == "__main__":
    ac.eztrim(src, [(289, 0)], path, "Kaguya2_01_cut.aac")
