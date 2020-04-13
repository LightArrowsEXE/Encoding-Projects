#!/usr/bin/env python3
import acsuite as acs
import lvsfunc as lvf
ac = acs.AC()


path = r'01/[Erai-raws] Kaguya-sama wa Kokurasetai! Tensai-tachi no Renai Zunousen 2 - 01 [1080p]'
src = lvf.src(path)

if __name__ == "__main__":
    ac.eztrim(src, [(289, 0)], path[:-4] + "_Track02.aac", "Kaguya2_01_cut.aac")
