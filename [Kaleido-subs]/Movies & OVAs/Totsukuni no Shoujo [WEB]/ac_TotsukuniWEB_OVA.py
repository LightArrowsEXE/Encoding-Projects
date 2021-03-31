#!/usr/bin/env python3
import ntpath

import lvsfunc as lvf
from acsuite import eztrim

# We want it to match with the web audio
path = r"[Kaleido-DDY] Totsukuni no Shoujo OVA (DVD 480p FLAC).mkv"
src = lvf.src(path)

if __name__ == "__main__":
    eztrim(src, (0, 13551), path, f"{ntpath.basename(__file__)[3:-3]}_cut.wav", ffmpeg_path='')  # noqa
