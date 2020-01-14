#!/usr/bin/env python3
import acsuite
import lvsfunc as lvf
ac = acsuite.AC()


path = r'DVDISO/(DVDISO)(アニメ) 鉄腕バーディー DECODE VOLUME05 (080128)(iso+mds+jpg)/TETSUWAN_BIRDY_05.d2v'
src = lvf.src(path)

if __name__ == "__main__":
    ac.eztrim(src, [(49053, 91626)], "DVDISO/(DVDISO)(アニメ) 鉄腕バーディー DECODE VOLUME05 (080128)(iso+mds+jpg)/TETSUWAN_BIRDY_05 Ta0 stereo 1536 kbps DELAY 0 ms.w64", "BirdyDecodeDVD_09_cut.wav")
