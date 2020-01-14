#!/usr/bin/env python3
import acsuite
import lvsfunc as lvf
ac = acsuite.AC()


path = r'DVDISO/(DVDISO)(アニメ) 鉄腕バーディー DECODE VOLUME02 (081022)(iso+mds+jpg)/TETSUWAN_BIRDY_02.d2v'
src = lvf.src(path)

if __name__ == "__main__":
    ac.eztrim(src, [(49055, 91628)], "DVDISO/(DVDISO)(アニメ) 鉄腕バーディー DECODE VOLUME02 (081022)(iso+mds+jpg)/TETSUWAN_BIRDY_02 Ta0 stereo 1536 kbps DELAY 0 ms.w64", "BirdyDecodeDVD_03_cut.wav")
