#!/usr/bin/env python3
import os
import acsuite as acs
import lvsfunc as lvf
ac = acs.AC()


path = r'04/[Erai-raws] 22-7 - 04 [1080p].mkv'
src = lvf.src(path)

if __name__ == "__main__":
    ac.eztrim(src, [(290, 0)], f"{os.path.splitext(path)[0]}_Track02.aac", f"{__file__[:-3]}_cut.aac")
