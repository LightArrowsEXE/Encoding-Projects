from functools import partial

import kagefunc as kgf
import lvsfunc as lvf
import vapoursynth as vs
import vardefunc as vdf
from vsutil import depth, get_y, iterate, join, plane

core = vs.core


def placebo_debander(clip: vs.VideoNode, grain: int = 4, **deband_args) -> vs.VideoNode:
    return join([  # Still not sure why splitting it up into planes is faster, but hey!
        core.placebo.Deband(plane(clip, 0), grain=grain, **deband_args),
        core.placebo.Deband(plane(clip, 1), grain=0, **deband_args),
        core.placebo.Deband(plane(clip, 2), grain=0, **deband_args)
    ])


# Common args
scale_args = dict(height=868, kernel=lvf.kernels.Bicubic())
deband_args = dict(iterations=2, threshold=3, radius=14)


# First frame of ED. OP credits are not 1080p
ed_offset = 0
edstart = 29971


start, end = 0, -32
path = r"BDMV/[BDMV][210120][GREAT PRETENDER][Vol.2]/GREAT_PRETENDER_CASE_2/BDMV/STREAM/00008.m2ts"
src = lvf.src(path)[start:end]
b = core.std.BlankClip(src, length=1)

if edstart is not False:
    src_NCED = lvf.src(r"BDMV/[BDMV][201216][GREAT PRETENDER][Vol.1]/GREAT_PRETENDER_CASE_1/BDMV/STREAM/00013.m2ts")[24+ed_offset:-27]
    ed_scomp = lvf.scomp(src[edstart:edstart+src_NCED.num_frames-1]+b, src_NCED+b, make_diff=True)


# Masking credits
ed_mask = vdf.diff_creditless_mask(src, src[edstart:edstart+src_NCED.num_frames-1],
                                   src_NCED, edstart, edstart+src_NCED.num_frames-1) \
                                   if edstart is not False else get_y(core.std.BlankClip(src))
descale_mask = depth(lvf.scale.descale(src, show_mask=True, **scale_args), 8)
credit_mask = core.std.Expr([ed_mask, descale_mask], expr='x y +')
credit_mask = iterate(credit_mask, core.std.Maximum, 3)
credit_mask = depth(credit_mask, 16).std.Binarize()

src = depth(src, 16)

dehalo_m = lvf.mask.halo_mask(src, rad=2)
blur = core.bilateral.Gaussian(src, sigma=0.7)
dehalo = core.std.MaskedMerge(src, blur, dehalo_m)

scaled = lvf.scale.descale(dehalo, **scale_args)

aa = lvf.sraa(scaled, rfactor=2.25, rep=13, downscaler=lvf.kernels.Bicubic().scale)
crecon = lvf.recon.chroma_reconstruct(aa)
merge = core.std.MaskedMerge(
    crecon, src.resize.Bicubic(format=crecon.format),
    get_y(credit_mask.resize.Bicubic(format=crecon.format)))

deband = placebo_debander(merge, grain=2, **deband_args)
grain = kgf.adaptive_grain(deband, 0.1)


out = grain
final = depth(out, 10)
final.set_output()


if __name__ == '__vapoursynth__':
    import ntpath
    import os
    import subprocess
    import kagefunc as kgf
    from acsuite import eztrim

    def keyframes(clip: vs.VideoNode, kf_path: str):
        if not os.path.isdir("keyframes"):
            os.makedirs("keyframes")
        kgf.generate_keyframes(clip, out_path=kf_path, header=False)

    try:
        keyframe_only
    except NameError:
        keyframe_only = False

    try:
        audio_only
    except NameError:
        audio_only = False

    try:
        no_audio
    except NameError:
        no_audio = False

    if keyframe_only is False or no_audio is True:
        audio_path = f"{ntpath.basename(__file__)[:-4]}_cut.mka"
        audio_path_out = f"{audio_path[:-4]}.flac"
        if not os.path.isfile(audio_path_out):
            print("Trimming and encoding audio")

            eztrim(src, (start, end), path, audio_path, ffmpeg_path='')
            subprocess.run(["eac3to", audio_path, "-log=NUL", audio_path_out])

            print(f"Deleting {audio_path}")
            try:
                os.remove(audio_path)
            except PermissionError:
                print(f"Failed to remove {audio_path}: PermissionError")

            if audio_only is True:
                exit()
            print("")

    kf_path = f"keyframes/{ntpath.basename(__file__)[:-4]}_keyframes.txt"
    if not os.path.isfile(kf_path):
        keyframes(src, kf_path)
        print("")
