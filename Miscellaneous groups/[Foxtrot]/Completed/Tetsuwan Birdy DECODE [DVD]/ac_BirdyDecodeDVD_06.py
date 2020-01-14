#!/usr/bin/env python3
import acsuite
import lvsfunc as lvf
ac = acsuite.AC()


path = r'DVDISO/(DVDISO)(アニメ) 鉄腕バーディー DECODE VOLUME04 (081217)(iso+mds+wav+cue+jpg)/TETSUWAN_BIRDY_04.d2v'
src = lvf.src(path)

if __name__ == "__main__":
    ac.eztrim(src, [(6450, 49008)], "DVDISO/(DVDISO)(アニメ) 鉄腕バーディー DECODE VOLUME04 (081217)(iso+mds+wav+cue+jpg)/TETSUWAN_BIRDY_04 Ta0 stereo 1536 kbps DELAY 0 ms.w64", "BirdyDecodeDVD_06_cut.wav")
