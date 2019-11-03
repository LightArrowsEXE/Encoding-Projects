#!/usr/bin/env python3
import vapoursynth as vs
import acsuite
import lvsfunc as lvf
core = vs.core
ac = acsuite.AC()


path = r'05/Fate Grand Order_ Zettai Majuu Sensen Babylonia - 05 (MX).d2v'
src = lvf.src(path)

if path.endswith('d2v'):
    src = core.vivtc.VDecimate(src)

if __name__ == "__main__":
    ac.eztrim(src, [(810,3902),(5580,14453),(15892,37972)], "05/Fate Grand Order_ Zettai Majuu Sensen Babylonia - 05 (MX) T112 stereo 255 kbps DELAY -369 ms.aac", "Babylonia_05_cut.aac")
