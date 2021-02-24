    #!/usr/bin/env python3

import vapoursynth as vs
import audiocutter
import lvsfunc as lvf
from subprocess import call
core = vs.core


ts_in = r"G:/src/!TEMP/Fairy Tail Zero BD/Fairy_Tail_Zero_Disc2/BDMV/STREAM/00027.m2ts"
src = lvf.src(ts_in)

ac = audiocutter.AudioCutter()

vid = ac.split(src, [(24,2181)])

ac.ready_qp_and_chapters(vid)

vid.set_output(0)
if __name__ == "__main__":
    ac.cut_audio(r'ac_FTOP22.m4a', audio_source=r'G:/src/!TEMP/Fairy Tail Zero BD/Fairy_Tail_Zero_Disc2/BDMV/STREAM/00027.m4a')
