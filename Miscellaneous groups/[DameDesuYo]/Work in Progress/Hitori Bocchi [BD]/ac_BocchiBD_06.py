#!/usr/bin/env python3

import vapoursynth as vs
import audiocutter
import lvsfunc as lvf
from subprocess import call


core = vs.core
ts_in = r'G:/src/[BDMV][190823][Hitoribocchi no Marumaru Seikatsu][Vol.2]/BDMV/STREAM/00008.m2ts'
src = lvf.src(ts_in)

if ts_in.endswith('d2v'):
    src = core.vivtc.VDecimate(src)

ac = audiocutter.AudioCutter()

vid = ac.split(src, [(24,src.num_frames-24)])

ac.ready_qp_and_chapters(vid)

vid.set_output(0)

if __name__ == "__main__":
    ac.cut_audio(r'BocchiBD_06_cut.m4a', audio_source=r'G:/src/[BDMV][190823][Hitoribocchi no Marumaru Seikatsu][Vol.2]/BDMV/STREAM/00008.m4a')
