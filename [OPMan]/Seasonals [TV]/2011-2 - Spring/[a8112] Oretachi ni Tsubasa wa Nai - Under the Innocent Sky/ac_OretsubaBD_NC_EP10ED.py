#!/usr/bin/env python3
import ntpath

import lvsfunc as lvf
from acsuite import eztrim

path = r"[BDMV] Ore-tachi ni Tsubasa wa Nai/[BDMV] [111026] 俺たちに翼はない Vol.5/ORETSUBA_05/BDMV/STREAM/00005.m2ts"
src = lvf.src(path)

if __name__ == "__main__":
    eztrim(src, (0, -24), path, f"{ntpath.basename(__file__)[3:-3]}_cut.mka", ffmpeg_path='')  # noqa
