#!/usr/bin/env python3
import ntpath

import lvsfunc as lvf
from acsuite import eztrim


path = r'BDMV/[KUNO-DIY][BDMV][CLANNAD][Blu-ray BOX Disc 1-5 Fin]/CLANNAD_5/BDMV/STREAM/00000.m2ts'
src = lvf.src(path)

if __name__ == "__main__":
    eztrim(src, (0, -48), path, f"{ntpath.basename(__file__)[3:-3]}_cut.mka", ffmpeg_path='')  # noqa
