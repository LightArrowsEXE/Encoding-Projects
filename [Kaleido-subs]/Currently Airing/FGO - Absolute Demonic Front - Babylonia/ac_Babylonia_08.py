#!/usr/bin/env python3
import vapoursynth as vs
import acsuite
import lvsfunc as lvf
core = vs.core
ac = acsuite.AC()


path = r'08/Fate Grand Order_ Zettai Majuu Sensen Babylonia - 08 (MX).d2v'
src = lvf.src(path)
src = lvf.decomb(src, True)
src.set_output()

if __name__ == "__main__":
    ac.eztrim(src, [(809,2630),(3590,20926),(21645,38692)], "08/Fate Grand Order_ Zettai Majuu Sensen Babylonia - 08 (MX) T112 stereo 255 kbps DELAY -326 ms.aac", "Babylonia_08_cut.aac")
