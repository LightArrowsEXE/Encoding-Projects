#!/usr/bin/env python3

import vapoursynth as vs
import audiocutter
import lvsfunc as lvf
from subprocess import call


core = vs.core
ts_in = r'BDMV/[BDMV][190424][Tate no Yuusha no Nariagari][Vol.1]/TATE_1_2/BDMV/STREAM/00013.m2ts'
src = lvf.src(ts_in)

ac = audiocutter.AudioCutter()

vid = ac.split(src, [(24, 2181)])

ac.ready_qp_and_chapters(vid)

vid.set_output(0)

if __name__ == "__main__":
    ac.cut_audio(r'ShieldbroBD_NCOP1_cut.m4a', audio_source=r'BDMV/[BDMV][190424][Tate no Yuusha no Nariagari][Vol.1]/TATE_1_2/BDMV/STREAM/00013.m4a')
