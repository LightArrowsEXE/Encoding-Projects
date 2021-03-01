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
scale_args = dict(height=868, kernel=lvf.kernels.Bicubic())
deband_args = dict(iterations=2, threshold=3, radius=14)


start, end = 24, -24
path = r"BDMV/[BDMV][201216][GREAT PRETENDER][Vol.1]/GREAT_PRETENDER_CASE_1/BDMV/STREAM/00014.m2ts"
src = lvf.src(path)[start:end]
src = depth(src, 16)

dehalo_m = lvf.mask.halo_mask(src, rad=2)
blur = core.bilateral.Gaussian(src, sigma=0.7)
dehalo = core.std.MaskedMerge(src, blur, dehalo_m)

scaled = lvf.scale.descale(dehalo, **scale_args)

aa = lvf.sraa(scaled, rfactor=2.25, rep=13, downscaler=lvf.kernels.Bicubic().scale)
crecon = lvf.recon.chroma_reconstruct(aa)

deband = placebo_debander(crecon, grain=2, **deband_args)
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
