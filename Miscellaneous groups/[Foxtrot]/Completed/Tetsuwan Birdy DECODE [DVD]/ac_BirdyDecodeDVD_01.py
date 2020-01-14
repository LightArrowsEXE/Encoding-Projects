#!/usr/bin/env python3
import acsuite
import lvsfunc as lvf
ac = acsuite.AC()


path = r'DVDISO/(DVDISO)(アニメ) 鉄腕バーディー DECODE VOLUME01 (080924)(iso+mds+jpg)/TETSUWAN_BIRDY_01.d2v'
src = lvf.src(path)

if __name__ == "__main__":
    ac.eztrim(src, [(4485, 47043)], "DVDISO/(DVDISO)(アニメ) 鉄腕バーディー DECODE VOLUME01 (080924)(iso+mds+jpg)/TETSUWAN_BIRDY_01 Ta0 stereo 1536 kbps DELAY 0 ms.w64", "BirdyDecodeDVD_01_cut.wav")
