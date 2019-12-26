#!/usr/bin/env python3
import vapoursynth as vs
import acsuite
import lvsfunc as lvf
core = vs.core
ac = acsuite.AC()


path = r'07/Fate Grand Order_ Zettai Majuu Sensen Babylonia - 07 (MX).d2v'
src = lvf.src(path)
src = lvf.decomb(src, True)
src.set_output()

if __name__ == "__main__":
    ac.eztrim(src, [(819,4439),(6118,20720),(22158,37982)], "07/Fate Grand Order_ Zettai Majuu Sensen Babylonia - 07 (MX) T112 stereo 253 kbps DELAY -356 ms.aac", "Babylonia_07_cut.aac")
