#!/usr/bin/env python3
import os
import subprocess

import lvsfunc as lvf
from acsuite import eztrim


path = r'BDMV/[BDMV][190402][マナリアフレンズ II]/BD/BDMV/STREAM/00008.m2ts'
src = lvf.src(path)

prev_start = 16688

if __name__ == "__main__":
    files = [f"{__file__[:-3]}_{i}_cut.wav" for i in 'ABCD']

    trims = [(24,prev_start), (0,24), (prev_start+240,0), (prev_start,prev_start+240)]

    print("\n[*] Trimming tracks")
    for f, t in zip(files, trims):
        print(f"    [+] Trimming {f} with trims {t}")
        eztrim(src, t, f"{os.path.splitext(path)[0]}.wav", f, quiet=True)

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
    print("   [+] Tracks successfully concatinated")

    print("\n[*] Removing files")
    for f in files:
        print(f"    [-] Removing {f}")

        try:
            os.remove(f)
        except FileNotFoundError:
            print(f"    [*] Failed to remove {f}")

    try:
        os.remove(f"{__file__[:-3]}_concat.txt")
    except FileNotFoundError:
        print(f"    [*] Failed to remove {__file__[:-3]}_concat.txt")

    print("\n[*] Done")
