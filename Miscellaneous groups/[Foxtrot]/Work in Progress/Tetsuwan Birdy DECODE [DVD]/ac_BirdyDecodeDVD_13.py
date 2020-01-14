#!/usr/bin/env python3
import acsuite
import lvsfunc as lvf
ac = acsuite.AC()


path = r'DVDISO/(DVDISO)(アニメ) 鉄腕バーディー DECODE VOLUME07 (090325)(iso+mds+jpg)/TETSUWAN_BIRDY_07.d2v'
src = lvf.src(path)

if __name__ == "__main__":
    ac.eztrim(src, [(49053, 90726)], "DVDISO/(DVDISO)(アニメ) 鉄腕バーディー DECODE VOLUME07 (090325)(iso+mds+jpg)/TETSUWAN_BIRDY_07 Ta0 stereo 1536 kbps DELAY 0 ms.w64", "BirdyDecodeDVD_13_cut.wav")
