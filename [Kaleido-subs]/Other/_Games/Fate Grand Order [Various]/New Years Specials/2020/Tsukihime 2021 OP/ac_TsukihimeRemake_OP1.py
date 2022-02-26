#!/usr/bin/env python3
import os
from acsuite import eztrim
import lvsfunc as lvf


path = r'Fate Project 2020.ts.dgi'
src = lvf.src(path)

if __name__ == "__main__":
    eztrim(src, (203498, 206645), f"{os.path.splitext(path)[0]}.aac", f"{__file__[:-3]}_cut.aac", ffmpeg_path='')
