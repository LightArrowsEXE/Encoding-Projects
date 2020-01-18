#!/usr/bin/env python3
import vapoursynth as vs
import acsuite
import lvsfunc as lvf
ac = acsuite.AC()
core = vs.core


path = r'BDMV/[DVDISO][アニメ] ひぐらしのなく頃に ファンディスク/[DVDISO][070622] ひぐらしのなく頃に FANDISC Ⅰ/[FCBP-0061EX] SPECIAL EDITION/DVD_VIDEO.d2v'
src = lvf.src(path)
src = core.vivtc.VDecimate(src)

if __name__ == "__main__":
    ac.eztrim(src, [(36266, 39024)], path[:-13]+"DVD_VIDEO Ta0 stereo 1536 kbps DELAY 0 ms.w64", "Higurashi1DVD_NCED1_cut.wav")
