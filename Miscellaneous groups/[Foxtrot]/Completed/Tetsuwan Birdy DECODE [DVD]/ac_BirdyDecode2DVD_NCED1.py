#!/usr/bin/env python3
import acsuite
import lvsfunc as lvf
ac = acsuite.AC()


path = r'DVDISO/Tetsuwan_Birdy_THE_CIPHER/TETSUWAN_BIRDY02_07.d2v'
src = lvf.src(path)

if __name__ == "__main__":
    ac.eztrim(src, [(104603, 107299)], "DVDISO/Tetsuwan_Birdy_THE_CIPHER/TETSUWAN_BIRDY02_07 Ta0 stereo 1536 kbps DELAY 0 ms.w64", "BirdyDecode2DVD_NCED1_cut.wav")
