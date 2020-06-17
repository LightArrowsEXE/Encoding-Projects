#!/usr/bin/env python3
import os
from acsuite import eztrim
import lvsfunc as lvf


path = r'DVDISO/(DVDISO)(アニメ) 鉄腕バーディー DECODE VOLUME06 (090225)(iso+mds+jpg)/TETSUWAN_BIRDY_06.d2v'
src = lvf.src(path)

if __name__ == "__main__":
    eztrim(src, (49053, 91626), f"{os.path.splitext(path)[0]} Ta0 stereo 1536 kbps DELAY 0 ms.w64", f"{__file__[:-3]}_cut.wav")
