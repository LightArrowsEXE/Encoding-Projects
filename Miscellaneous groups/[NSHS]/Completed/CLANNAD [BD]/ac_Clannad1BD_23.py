#!/usr/bin/env python3
import ntpath
import os
import subprocess

import lvsfunc as lvf
from acsuite import eztrim


path_a = r'BDMV/[KUNO-DIY][BDMV][CLANNAD][Blu-ray BOX Disc 1-5 Fin]/CLANNAD_5/BDMV/STREAM/00002.m2ts'
path_b = r'BDMV/[KUNO-DIY][BDMV][CLANNAD][Blu-ray BOX Disc 1-5 Fin]/CLANNAD_5/BDMV/STREAM/00004.m2ts'

src_a = lvf.src(path_a)
src_b = lvf.src(path_b)

if __name__ == "__main__":
    paths = [path_a, path_b]
    clips = [src_a, src_b]
    files = [f"{ntpath.basename(__file__)[3:-3]}_{i}_cut.mka" for i in 'AB']

    print("\n[*] Trimming tracks")
    for c, p, f in zip(clips, paths, files):
        print(f"    [+] Trimming {f}")
        eztrim(c, (0, -48), p, f, quiet=True)

    print("\n[*] Writing concact file")
    concat = open(f"{ntpath.basename(__file__)[3:-3]}_concat.txt", "w")
    for f in files:
        print(f"    [+] Appending {f[:-4]}.wav")
        concat.write(f"file {f[:-4]}.wav\n")
    concat.close()

    print("\n[*] Concatinating trimmed tracks")
    subprocess.run([
        "ffmpeg", "-f", "concat",
        "-i", f"{ntpath.basename(__file__)[3:-3]}_concat.txt",
        "-c", "copy", f"{ntpath.basename(__file__)[3:-3]}_cut.mka"
    ])

    print("\n[*] Removing files")
    for f in files:
        print(f"    [-] Removing {f[:-4]}.wav")

        try:
            os.remove(f"{f[:-4]}.wav")
        except FileNotFoundError:
            print(f"    [*] Failed to remove {f[:-4]}.wav; file not found")

    try:
        os.remove(f"{ntpath.basename(__file__)[3:-3]}_concat.txt")
    except FileNotFoundError:
        print(f"    [*] Failed to remove {ntpath.basename(__file__)[3:-3]}_concat.txt; file not found")

    print("\n[*] Done")
