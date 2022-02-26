#!/usr/bin/env python3
import ntpath

import lvsfunc as lvf
from acsuite import eztrim

path = r"BDMV/Dimension.W.2015.ANiME.DUAL.COMPLETE.BLURAY-iFPD/Dimension W Box 3 German BD/BDMV/STREAM/00007.m2ts"
src = lvf.src(path)

if __name__ == "__main__":
    eztrim(src, (0, 0), path, f"{ntpath.basename(__file__)[3:-3]}_cut.mka", ffmpeg_path='')  # noqa
