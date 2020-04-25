#!/usr/bin/env python3
import vapoursynth as vs
import acsuite as acs
import lvsfunc as lvf
core = vs.core
ac = acs.AC()


path = r'BDMV/[BDMV][191127] Fate／kaleid liner Prisma☆Illya Prisma☆Phantasm/PRISMAPHANTASM_SP/BDMV/STREAM/00001.m2ts'
src = lvf.src(path)

if __name__ == "__main__":
    ac.eztrim(src, [([48, -24])], path, "IllyaOVABD_01_cut.wav")

src.set_output()
