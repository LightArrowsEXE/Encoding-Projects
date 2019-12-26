#!/usr/bin/env python3
import vapoursynth as vs
import acsuite
import lvsfunc as lvf
core = vs.core
ac = acsuite.AC()


path = r'06/Fate Grand Order_ Zettai Majuu Sensen Babylonia - 06 (MX).d2v'
src = lvf.src(path)
src = lvf.decomb(src, True)

if __name__ == "__main__":
    ac.eztrim(src, [(810,4070),(5747,19559),(20998,37973)], "06/Fate Grand Order_ Zettai Majuu Sensen Babylonia - 06 (MX) T112 stereo 263 kbps DELAY -335 ms.aac", "Babylonia_06_cut.aac")
