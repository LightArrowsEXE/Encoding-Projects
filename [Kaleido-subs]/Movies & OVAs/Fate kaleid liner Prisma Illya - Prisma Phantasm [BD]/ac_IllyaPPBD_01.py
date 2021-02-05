#!/usr/bin/env python3
import ntpath
import os
import subprocess

import lvsfunc as lvf
from acsuite import eztrim


path_a = 'BDMV/[BDMV][191127] Fate／kaleid liner Prisma☆Illya Prisma☆Phantasm/PRISMAPHANTASM_SP/BDMV/STREAM/00001.m2ts'
src_a = lvf.src(path_a)

path_b = 'BDMV/[BDMV][191127] Fate／kaleid liner Prisma☆Illya Prisma☆Phantasm/PRISMAPHANTASM_SP/BDMV/STREAM/00004.m2ts'
src_b = lvf.src(path_b)

if __name__ == "__main__":
    paths = [path_a, path_b]
    clips = [src_a, src_b]
    files = [f"{__file__[:-3]}_{i}_cut.wav" for i in 'AB']
    trims = [(48, -24), (24, -24)]

    print("\n[*] Trimming tracks")
    for path, f, t, src in zip(paths, files, trims, clips):
        print(f"    [+] Trimming {f} with trims {t}")
        eztrim(src, t, path, f, quiet=True)

    print("\n[*] Writing concact file")
    concat = open(f"{__file__[:-3]}_concat.txt", "w")
    for f in files:
        print(f"    [+] Adding {f}")
        concat.write(f"file {f}\n")
    concat.close()

    print("\n[*] Concatinating trimmed tracks")
    subprocess.run(["ffmpeg", "-f", "concat", "-i", f"{__file__[:-3]}_concat.txt",
                            "-loglevel", "panic", "-stats",
                            "-c", "copy", f"{__file__[3:-3]}_cut.wav"])

    print("\n[*] Removing files")
    for f in paths:
        print(f"    [-] Removing {f}")

        try:
            os.remove(f)
        except FileNotFoundError or PermissionError:
            print(f"    [*] Failed to remove {f}")
