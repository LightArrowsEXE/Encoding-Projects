#!/usr/bin/env python3
import vapoursynth as vs
from acsuite import eztrim
import lvsfunc as lvf


path = r'08/Fate Grand Order_ Zettai Majuu Sensen Babylonia - 08 (MX).d2v'
src = lvf.src(path)
src = lvf.decomb(src, True)

if __name__ == "__main__":
    eztrim(src, [(809,2630),(3590,20926),(21645,38692)], "08/Fate Grand Order_ Zettai Majuu Sensen Babylonia - 08 (MX) T112 stereo 255 kbps DELAY -326 ms.aac", f"{__file__[:-3]}_cut.wav")
