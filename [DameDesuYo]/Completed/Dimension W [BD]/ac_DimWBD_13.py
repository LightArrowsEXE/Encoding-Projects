#!/usr/bin/env python3
import ntpath

import lvsfunc as lvf
from acsuite import eztrim

path = r"BDMV/DIMENSION_W_6/FullDisc/DIMENSION_W_6/BDMV/STREAM/00011.m2ts"
src = lvf.src(path)

if __name__ == "__main__":
    eztrim(src, (0, -24), path, f"{ntpath.basename(__file__)[3:-3]}_cut.mka", ffmpeg_path='')  # noqa
