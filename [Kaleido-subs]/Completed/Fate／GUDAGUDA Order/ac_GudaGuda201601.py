#!/usr/bin/env python3

import vapoursynth as vs
import audiocutter
import lvsfunc as lvf
from subprocess import call

# I love having to fuck around with audiocutter ranges
Part_A_1 = 141878+24; Part_A_2 = 144303+24
Part_B_1 = 151728+24; Part_B_2 = 154006+21
Part_C_1 = 170858+23; Part_C_2 = 172204+24
Part_D_1 = 180778+24; Part_D_2 = 182666+24
Part_E_1 = 200085+24; Part_E_2 = 202902+24

core = vs.core
ts_in = r'TV caps/Fate／Grand Order -First Order- Fate Project 大晦日TVスペシャル ～First & Next Order～ (BS11).ts.d2v'
src = lvf.src(ts_in)

ac = audiocutter.AudioCutter()

vid = ac.split(src, [(Part_A_1,Part_A_2),(Part_B_1,Part_B_2),(Part_C_1,Part_C_2),(Part_D_1,Part_D_2),(Part_E_1,Part_E_2)])

ac.ready_qp_and_chapters(vid)

vid.set_output(0)

if __name__ == "__main__":
    ac.cut_audio(r'GudaGuda201601.aac', audio_source=r'TV caps/Fate／Grand Order -First Order- Fate Project 大晦日TVスペシャル ～First & Next Order～ (BS11).mka')
