#!/usr/bin/env python3
import os
import acsuite as acs
import lvsfunc as lvf
ac = acs.AC()


path = r'05/[Erai-raws] 22-7 - 05 [1080p].mkv'
src = lvf.src(path)

if __name__ == "__main__":
    ac.eztrim(src, [(289, 0)], f"{os.path.splitext(path)[0]}_Track02.aac", f"{__file__[:-3]}_cut.aac")
