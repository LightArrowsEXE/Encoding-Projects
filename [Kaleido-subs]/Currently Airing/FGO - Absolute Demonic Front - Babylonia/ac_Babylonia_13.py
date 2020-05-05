#!/usr/bin/env python3
import acsuite as acs
import lvsfunc as lvf
ac = acs.AC()


path = r'13/[Erai-raws] Fate Grand Order - Zettai Majuu Sensen Babylonia - 13 [1080p].mkv'
src = lvf.src(path)

if __name__ == "__main__":
    ac.eztrim(src, [(289, 0)], path[:-4]+"wav", "Babylonia_13_cut.aac")
