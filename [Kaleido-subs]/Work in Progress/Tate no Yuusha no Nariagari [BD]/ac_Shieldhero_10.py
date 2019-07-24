#!/usr/bin/env python3

import vapoursynth as vs
import audiocutter
import lvsfunc as lvf
from subprocess import call


core = vs.core
ts_in = r'BDMV/[BDMV][190524][Tate no Yuusha no Nariagari][Vol.2]/TATE_2_1/BDMV/STREAM/00011.m2ts'
src = lvf.src(ts_in)

ac = audiocutter.AudioCutter()

vid = ac.split(src, [(0,34044)])

ac.ready_qp_and_chapters(vid)

vid.set_output(0)

if __name__ == "__main__":
    ac.cut_audio(r'ShieldbroBD_10_cut.m4a', audio_source=r'BDMV/[BDMV][190524][Tate no Yuusha no Nariagari][Vol.2]/TATE_2_1/BDMV/STREAM/00011.m4a')
