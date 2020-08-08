#!/usr/bin/env python3
import vapoursynth as vs
from acsuite import eztrim
import lvsfunc as lvf


path = r'07/Fate Grand Order_ Zettai Majuu Sensen Babylonia - 07 (MX).d2v'
src = lvf.src(path)
src = lvf.decomb(src, True)

if __name__ == "__main__":
    eztrim(src, [(819,4439),(6118,20720),(22158,37982)], "07/Fate Grand Order_ Zettai Majuu Sensen Babylonia - 07 (MX) T112 stereo 253 kbps DELAY -356 ms.aac", f"{__file__[:-3]}_cut.wav")
