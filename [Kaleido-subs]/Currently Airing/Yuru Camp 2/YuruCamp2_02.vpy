import ntpath
from glob import glob

import debandshit as dbs
import havsfunc as haf
import insaneAA as insaa
import kagefunc as kgf
import lvsfunc as lvf
import mvsfunc as mvf
import G41Fun as g41
import vapoursynth as vs
from finedehalo import fine_dehalo
from vsutil import depth, get_y, iterate, scale_value

core = vs.core


c = dict(left=4, right=4, top=4, bottom=4)

# Scenefiltering
str_deband = [(12988, 14043), (14086, 15201), (15250, 16065), (16177, 17069), (17196, 17567), (17856, 17903), (18570, 18971), (19326, 19493), (20095, 20148), (21253, 21408), (21565, 21960), (22153, 22692), (22813, 23002), (23149, 23508)]


src = lvf.src(glob(f'{ntpath.basename(__file__)[-6:-4]}/*.mkv')[0])
src = depth(src, 16)


lmask = kgf.retinex_edgemask(src).std.Inflate().std.Maximum().std.CropRel(**c).std.AddBorders(**c)
aa = core.std.MaskedMerge(src, g41.daamod(src, passes=5), lmask)
dehalo = fine_dehalo(aa, rx=2.4, ry=2.2, ref=src, darkstr=0, brightstr=0.9)

detail_mask = lvf.denoise.detail_mask(dehalo, sigma=0.7, brz_a=0.0125, brz_b=0.025)
deband_wk = core.neo_f3kdb.Deband(dehalo, range=15, y=32, cb=24, cr=24, grainy=24, grainc=0, sample_mode=4)
deband_str = dbs.f3kpf(dehalo, range=14, y=48, cb=48)
deband = lvf.rfs(deband_wk, deband_str, str_deband)
deband = core.std.MaskedMerge(deband, dehalo, detail_mask)

grain_wk = kgf.adaptive_grain(deband, 0.15, luma_scaling=4)
grain_str = kgf.adaptive_grain(deband, 0.25, luma_scaling=1)
grain = lvf.rfs(grain_wk, grain_str, str_deband)


out = grain
final = depth(out, 10)
final.set_output()


if __name__ == '__vapoursynth__':
    import ntpath
    import os

    def keyframes(clip: vs.VideoNode, kf_path: str):
        if os.path.isdir("keyframes") is False:
            os.makedirs("keyframes")
        kgf.generate_keyframes(clip, out_path=kf_path, header=False)

    kf_path = f"keyframes/{ntpath.basename(__file__)[:-4]}_keyframes.txt"
    if os.path.isfile(kf_path) is False:
        keyframes(src, kf_path)
