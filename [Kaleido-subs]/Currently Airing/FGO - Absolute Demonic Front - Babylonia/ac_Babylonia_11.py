#!/usr/bin/env python3
import acsuite as acs
import lvsfunc as lvf
ac = acs.AC()


path = r'11/Fate Grand Order Absolute Demonic Front Babylonia E11 [1080p][AAC][JapDub][GerSub][Web-DL].mkv'
src = lvf.src(path)

if __name__ == "__main__":
    ac.eztrim(src, [(0, 0)], path[:-4]+"wav", "Babylonia_11_cut.aac")
