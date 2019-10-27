#!/usr/bin/env python3
import acsuite
import lvsfunc as lvf
ac = acsuite.AC()


path = r'04/Fate Grand Order_ Zettai Majuu Sensen Babylonia - 04 (MX).d2v'
src = lvf.src(path)

if __name__ == "__main__":
    ac.eztrim(src, [(1017,5207),(7306,25317),(27114,47466)], "04/Fate Grand Order_ Zettai Majuu Sensen Babylonia - 04 (MX) T112 stereo 255 kbps DELAY -352 ms.aac", "Babylonia_04_cut.aac")
