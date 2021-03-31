import adptvgrnMod as adp
import havsfunc as haf
import lvsfunc as lvf
import mvsfunc as mvf
import vapoursynth as vs
import xvs as x
from finedehalo import fine_dehalo
from vsutil import depth, get_w, get_y, join, plane

core = vs.core


def placebo_debander(clip: vs.VideoNode, grain: int = 4, **deband_args) -> vs.VideoNode:
    return join([  # Still not sure why splitting it up into planes is faster, but hey!
        core.placebo.Deband(plane(clip, 0), grain=grain, **deband_args),
        core.placebo.Deband(plane(clip, 1), grain=0, **deband_args),
        core.placebo.Deband(plane(clip, 2), grain=0, **deband_args)
    ])


deband_args = dict(iterations=2, threshold=6, radius=8, grain=12)


src = lvf.src(r"src/The.Girl.From.The.Other.Side.2019.1080p.WEB-DL.AAC2.0.H.264-aKraa.mkv")[144:-48]
src = depth(src, 16)


denoise = haf.SMDegrain(src, thSAD=100)

dehalo_m = lvf.mask.halo_mask(denoise, 3) \
    .std.Inflate().std.Maximum().std.Maximum()
den_ref = mvf.BM3D(denoise, sigma=12)
edgefix = core.bilateral.Bilateral(den_ref, sigmaS=1.6, sigmaR=6/255)
dehalo = core.std.MaskedMerge(denoise, edgefix, dehalo_m)
dehalo = fine_dehalo(dehalo, thmi=24, thma=255, brightstr=0.7, darkstr=0)

amask = lvf.mask.adaptive_mask(dehalo, 12)
cwarp = x.WarpFixChromaBlend(dehalo, depth=32, thresh=184)
cwarp = core.std.MaskedMerge(cwarp, dehalo, amask)

aa = lvf.aa.nneedi3_clamp(cwarp, strength=1.6)
darken = haf.FastLineDarkenMOD(aa, strength=56)

deband = placebo_debander(darken, grain=8)
grain = adp.adptvgrnMod(deband, static=True, strength=1.85, cstrength=0, luma_scaling=4, size=1.35)


out = grain
final = depth(out, 10)
final.set_output()


if __name__ == '__vapoursynth__':
    import ntpath
    import os

    import kagefunc as kgf

    def keyframes(clip: vs.VideoNode, kf_path: str):
        if not os.path.isdir("keyframes"):
            os.makedirs("keyframes")
        kgf.generate_keyframes(clip, out_path=kf_path, header=False)

    kf_path = f"keyframes/{ntpath.basename(__file__)[:-4]}_keyframes.txt"
    if not os.path.isfile(kf_path):
        keyframes(src, kf_path)
