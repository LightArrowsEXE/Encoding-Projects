"""
Lazy script. Probably still gonna be way better than most releases tho lmfao
"""
import havsfunc as haf
import kagefunc as kgf
import lvsfunc as lvf
import vapoursynth as vs
from vsutil import depth, join, plane

core = vs.core


def placebo_debander(clip: vs.VideoNode, grain: int = 4, **deband_args) -> vs.VideoNode:
    return join([  # Still not sure why splitting it up into planes is faster, but hey!
        core.placebo.Deband(plane(clip, 0), grain=grain, **deband_args),
        core.placebo.Deband(plane(clip, 1), grain=0, **deband_args),
        core.placebo.Deband(plane(clip, 2), grain=0, **deband_args)
    ])


# Common args
deband_args = dict(grain=2, iterations=2, threshold=3, radius=14)


src = lvf.src(r"BDMV/[BDMV] Uzaki-chan Wants to Hang Out! Volume 1/UZAKICHAN_WA_ASOBITAI_01/BDMV/STREAM/00017.m2ts")[24:-24]
src = depth(src, 16)

denoise = haf.SMDegrain(src, thSAD=80)
aa = core.znedi3.nnedi3(denoise, field=0, dh=True, nsize=4, nns=4, qual=2, pscrn=2)
aa = core.resize.Bicubic(aa, src.width, src.height, src_top=0.5)
ec = haf.EdgeCleaner(aa, strength=3, rmode=13, hot=True)

deband_mask = lvf.mask.detail_mask(ec, sigma=0.8, brz_a=0.008, brz_b=0.015)
deband = placebo_debander(ec, **deband_args)
deband = core.std.MaskedMerge(deband, ec, deband_mask)

grain = kgf.adaptive_grain(deband, 0.1, luma_scaling=4)


out = grain
final = depth(out, 10)
final.set_output()


if __name__ == '__vapoursynth__':
    import ntpath
    import os

    def keyframes(clip: vs.VideoNode, kf_path: str):
        if not os.path.isdir("keyframes"):
            os.makedirs("keyframes")
        kgf.generate_keyframes(clip, out_path=kf_path, header=False)

    kf_path = f"keyframes/{ntpath.basename(__file__)[:-4]}_keyframes.txt"
    if not os.path.isfile(kf_path):
        keyframes(src, kf_path)
