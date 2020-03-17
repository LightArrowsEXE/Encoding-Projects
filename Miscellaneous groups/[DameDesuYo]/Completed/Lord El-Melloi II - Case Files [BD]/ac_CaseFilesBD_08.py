#!/usr/bin/env python3
import acsuite as acs
import lvsfunc as lvf
ac = acs.AC()


path = r'BDMV/[BDMV][アニメ][191204] ロード・エルメロイII世の事件簿 -魔眼蒐集列車 Grace note- 4/BDROM/BDMV/STREAM/00001.m2ts'
src = lvf.src(path)

if __name__ == "__main__":
    ac.eztrim(src, [(24, -24)], path[:-4]+"wav", "CaseFilesBD_08_cut.wav")
