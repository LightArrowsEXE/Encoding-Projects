#!/usr/bin/env python3
import ntpath

import lvsfunc as lvf
from acsuite import eztrim

path = r"[BDMV] Ore-tachi ni Tsubasa wa Nai/[BDMV] [110824] 俺たちに翼はない Vol.3/ORETSUBA_03/BDMV/STREAM/00003.m2ts"
src = lvf.src(path)

if __name__ == "__main__":
    eztrim(src, (0, -26), path, f"{ntpath.basename(__file__)[3:-3]}_cut.mka", ffmpeg_path='')  # noqa
