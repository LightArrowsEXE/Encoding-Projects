#!/usr/bin/env python3
import ntpath

import lvsfunc as lvf
from acsuite import eztrim

path = r"BDMV/[BDMV] Uzaki-chan Wants to Hang Out! Volume 2/UZAKICHAN_WA_ASOBITAI_02/BDMV/STREAM/00012.m2ts"  # noqa
src = lvf.src(path)

if __name__ == "__main__":
    eztrim(src, (24, -24), path, f"{ntpath.basename(__file__)[3:-3]}_cut.mka", ffmpeg_path='')  # noqa
