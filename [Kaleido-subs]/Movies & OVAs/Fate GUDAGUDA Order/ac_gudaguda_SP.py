#!/usr/bin/env python3
import ntpath
import os

import lvsfunc as lvf
from acsuite import eztrim


path = r'Fate Grand Order -First Order- Fate Project (BS11).dgi'
src = lvf.src(path)
dec = lvf.deinterlace.decomb(src, TFF=True)

if __name__ == "__main__":
    eztrim(dec, [
        (113503, 115443), (121382, 123205), (136688, 137764),
        (144624, 146134), (160069, 162322)
    ], "Fate Grand Order -First Order- Fate Project (BS11) PID 141  DELAY -348ms.aac",
       f"{ntpath.basename(__file__)[3:-3]}_cut.mka",
       ffmpeg_path='')
