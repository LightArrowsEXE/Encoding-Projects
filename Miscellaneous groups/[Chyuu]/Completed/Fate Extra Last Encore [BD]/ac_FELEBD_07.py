#!/usr/bin/env python3
import os
import subprocess

import lvsfunc as lvf
from acsuite import eztrim


"""
    What makes this episode different to cut from other episodes
    is that the ED was separated. We merge them here by trimming multiple times
    and recombining them after.

    This was reworked from my (updated) Manaria audio cutting script.
"""

paths = [r'BDMV/Fate Extra Last Encore/Vol3/BDROM/BDMV/STREAM/00001.m2ts',
         r'BDMV/Fate Extra Last Encore/Vol3/BDROM/BDMV/STREAM/00010.m2ts',
         r'BDMV/Fate Extra Last Encore/Vol3/BDROM/BDMV/STREAM/00001.m2ts']

files = [f"{__file__[:-3]}_{i}_cut.wav" for i in 'ABC']

trims = [(24, 33429), (24, -24), (33429, 0)]

if __name__ == "__main__":
    print("\n[*] Trimming tracks")
    for p, f, t in zip(paths, files, trims):
        print(f"    [+] Trimming {f} with trims {t}")
        eztrim(lvf.src(p), t, f"{os.path.splitext(p)[0]}.wav", f, quiet=True)

    print("\n[*] Writing concact file")
    concat = open(f"{__file__[:-3]}_concat.txt", "w")
    for f in files:
        print(f"    [+] Adding {f}")
        concat.write(f"file {f}\n")
    concat.close()

    print("\n[*] Concatinating trimmed tracks")
    subprocess.run(["ffmpeg", "-f", "concat", "-i",
                              f"{__file__[:-3]}_concat.txt",
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
