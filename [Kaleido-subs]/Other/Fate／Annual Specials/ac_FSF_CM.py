#!/usr/bin/env python3
import vapoursynth as vs
import acsuite
import lvsfunc as lvf
core = vs.core
ac = acsuite.AC()


path = r'1912312200_【ＢＳ１１イレブン】Fate Project 大晦日TVスペシャル 2019【BS11 大晦日超アニメスペシャル！】.d2v'
src = lvf.src(path)
src = lvf.decomb(src, True)

if __name__ == "__main__":
    ac.eztrim(src, [(80566,81285)], "src/1912312200_【ＢＳ１１イレブン】Fate Project 大晦日TVスペシャル 2019【BS11 大晦日超アニメスペシャル！】 T141 stereo 255 kbps DELAY -360 ms.aac", "FSF_CM_cut.aac")
