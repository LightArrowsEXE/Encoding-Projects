import ntpath
import os

import havsfunc as haf
import kagefunc as kgf
import lvsfunc as lvf
import vapoursynth as vs
from vsutil import depth, get_w, join, plane

core = vs.core

shader = 'FSRCNNX_x2_56-16-4-1.glsl'
if os.path.exists(shader) is False:
    hookpath = r"mpv\shaders\FSRCNNX_x2_56-16-4-1.glsl"
    shader = os.path.join(os.getenv("APPDATA"), hookpath)


def placebo_debander(clip: vs.VideoNode, grain: int = 4, **deband_args) -> vs.VideoNode:
    return join([  # Still not sure why splitting it up into planes is faster, but hey!
        core.placebo.Deband(plane(clip, 0), grain=grain, **deband_args),
        core.placebo.Deband(plane(clip, 1), grain=0, **deband_args),
        core.placebo.Deband(plane(clip, 2), grain=0, **deband_args)
    ])


# Common args
deband_args = dict(iterations=2, threshold=5, radius=14)

# `--arg` passed through vspipe (see ``settings.sh``)
try:
    enc_1080  # noqa
    upscaled = True
except NameError:
    upscaled = False


src = lvf.src(r"BDMV/DIMENSION_W_5/FullDisc/DIMENSION_W_5/BDMV/STREAM/00010.m2ts")[24:-24]
src = depth(src, 32)

scaled = lvf.scale.descale(src, height=972, kernel=lvf.kernels.Bicubic(0, 1))
scaled = depth(scaled, 16)

denoise = haf.SMDegrain(scaled, tr=1, thSAD=150, prefilter=3, search=3, contrasharp=True, RefineMotion=True)

dehalo_m = lvf.mask.halo_mask(denoise)
blur = core.bilateral.Gaussian(denoise, sigma=0.4)
dehalo = core.std.MaskedMerge(denoise, blur, dehalo_m)

aa = lvf.sraa(dehalo, rfactor=1.8, rep=13, downscaler=lvf.kernels.Bicubic().scale)

deband = placebo_debander(aa, grain=0, **deband_args)

if upscaled:
    out = deband
else:
    out = core.resize.Bicubic(deband, get_w(720), 720, vs.YUV444P16)


final = depth(out, 10)
final.set_output()


if __name__ == '__vapoursynth__':
    import os

    def keyframes(clip: vs.VideoNode, kf_path: str):
        if not os.path.isdir("keyframes"):
            os.makedirs("keyframes")
        kgf.generate_keyframes(clip, out_path=kf_path, header=False)

    kf_path = f"keyframes/{ntpath.basename(__file__)[:-4]}_keyframes.txt"
    if not os.path.isfile(kf_path):
        keyframes(src, kf_path)
