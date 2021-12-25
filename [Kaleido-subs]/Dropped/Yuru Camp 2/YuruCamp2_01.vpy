import ntpath
import os
from glob import glob

import havsfunc as haf
import insaneAA as insaa
import kagefunc as kgf
import lvsfunc as lvf
import mvsfunc as mvf
import vapoursynth as vs
from finedehalo import fine_dehalo
from vsutil import depth

core = vs.core


def keyframes(clip: vs.VideoNode, kf_path: str):
    if os.path.isdir("keyframes") is False:
        os.makedirs("keyframes")
    kgf.generate_keyframes(clip, out_path=kf_path, header=False)


src = lvf.src(glob(f'{ntpath.basename(__file__)[-6:-4]}/*.mkv')[0])
src = depth(src, 16)


ref = haf.SMDegrain(src, tr=1, thSAD=175, prefilter=3, search=3, contrasharp=True, RefineMotion=True)
denoise = mvf.BM3D(src, sigma=[1.25, 1.5], radius1=1, profile1='lc', psample=0, ref=ref)


aa = insaa.rescale(src, dx=1920, dy=1080, nnedi3_mode=2, pscrn=1, nsize=6)
dehalo = fine_dehalo(aa, rx=2.2, ry=2, darkstr=0, brightstr=0.6)

detail_mask = lvf.denoise.detail_mask(dehalo, sigma=0.7, brz_a=0.0125, brz_b=0.025)
deband = core.neo_f3kdb.Deband(dehalo, range=15, y=32, cb=24, cr=24, grainy=24, grainc=0, sample_mode=4)
deband = core.std.MaskedMerge(deband, dehalo, detail_mask)

grain = kgf.adaptive_grain(deband, 0.15, luma_scaling=4)


out = grain
final = depth(out, 10)
final.set_output()


if __name__ == '__vapoursynth__':
    kf_path = f"keyframes/{ntpath.basename(__file__)[:-4]}_keyframes.txt"
    if os.path.isfile(kf_path) is False:
        print("Keyframe file not found; generating")
        keyframes(src, kf_path)
