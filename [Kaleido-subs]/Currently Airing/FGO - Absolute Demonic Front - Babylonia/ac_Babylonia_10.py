#!/usr/bin/env python3
import acsuite as acs
import lvsfunc as lvf
ac = acs.AC()


path = r'10/[Erai-raws] Fate Grand Order - Zettai Majuu Sensen Babylonia - 10 [1080p][Multiple Subtitle].mkv'
src = lvf.src(path)

if __name__ == "__main__":
    ac.eztrim(src, [(289, 0)], path[:-4]+"wav", "Babylonia_10_cut.aac")
