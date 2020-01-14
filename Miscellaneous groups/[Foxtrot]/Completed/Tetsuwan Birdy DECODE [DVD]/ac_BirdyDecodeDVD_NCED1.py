#!/usr/bin/env python3
import acsuite
import lvsfunc as lvf
ac = acsuite.AC()


path = r'DVDISO/Tetsuwan_Birdy_THE_CIPHER/TETSUWAN_BIRDY02_07.d2v'
src = lvf.src(path)

if __name__ == "__main__":
    ac.eztrim(src, [(99057, 101755)], "DVDISO/Tetsuwan_Birdy_THE_CIPHER/TETSUWAN_BIRDY02_07 Ta0 stereo 1536 kbps DELAY 0 ms.w64", "BirdyDecodeDVD_NCED1_cut.wav")
