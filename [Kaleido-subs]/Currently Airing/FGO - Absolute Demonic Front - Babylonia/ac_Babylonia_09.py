#!/usr/bin/env python3
import acsuite as acs
import lvsfunc as lvf
ac = acs.AC()


path = r'09/Fate Grand Order Absolute Demonic Front Babylonia E09 [1080p][AAC][JapDub][GerSub][Web-DL].mkv'
src = lvf.src(path)

if __name__ == "__main__":
    ac.eztrim(src, [(0, 0)], path[:-4]+"wav", "Babylonia_09_cut.aac")

# Note for future episodes:
#   Switching from TV audio to Wakanim audio. Should match without trims.