import ntpath
import os

import awsmfunc as awsm
import debandshit as dbs
import havsfunc as haf
import kagefunc as kgf
import lvsfunc as lvf
import mvsfunc as mvf
import vapoursynth as vs
import vardefunc as vdf
import xvs
from finedehalo import fine_dehalo
from vsutil import depth, get_y, iterate, join, plane

core = vs.core

shader = 'FSRCNNX_x2_56-16-4-1.glsl'
if os.path.exists(shader) is False:
    hookpath = "mpv/shaders/FSRCNNX_x2_56-16-4-1.glsl"
    shader = os.path.join(os.getenv("APPDATA"), hookpath)


def read_credit_mask(index: int, framerange: str, src_clip: vs.VideoNode) -> tuple:
    # Code for reading a bunch of custom-made credit masks, since descaling doesn't actually catch those ???
    return (framerange, lvf.src(f'assets/{ntpath.basename(__file__)[-6:-4]}/credit_mask{index}.png', ref=src_clip))


# Common args
scale_args = dict(height=936, kernel=lvf.kernels.Spline36())

# First frame of first cut
opstart = False
edstart = False

op_offset = 0
ed_offset = 0

# Sometimes I can't mask the credits nicely with automations
credit_mask_ranges = []

# Not do any scaling (and by extension AA/Dehalo) on these ranges
noscale_ranges = []


src = lvf.src(r"BDMV/[BDMV][アニメ][210127][MAJO_NO_TABITABI_1][Blu-Ray BOX 上]/BDMV/STREAM/00007.m2ts")[24:-24]
ef = awsm.bbmod(src, top=1, bottom=1, left=1, right=1)
ef = depth(ef, 32)

lmask = core.std.Sobel(get_y(ef))
lmask = iterate(lmask, core.std.Inflate, 5)
descaled = lvf.scale.descale(ef, upscaler=None, **scale_args)

dehalo = fine_dehalo(descaled, rx=1, darkstr=0)
aa = lvf.sraa(dehalo, rfactor=2.25, rep=13, downscaler=lvf.kernels.Bicubic().scale)

upscaled = vdf.fsrcnnx_upscale(aa, shader_file=shader)
scaled = join([upscaled, plane(ef, 1), plane(ef, 2)])
# Need to go down to 16bit or it gives odd white lines (???)
scaled = core.std.MaskedMerge(depth(ef, 16), depth(scaled, 16), depth(lmask, 16))
scaled = lvf.rfs(scaled, depth(ef, 16), noscale_ranges)


adap_mask = lvf.mask.adaptive_mask(scaled, luma_scaling=4)
ref = haf.SMDegrain(scaled, tr=1, thSAD=75, prefilter=3, search=3)
denoise = mvf.BM3D(scaled, ref=ref, sigma=[0.8, 1.2])
denoise = core.std.MaskedMerge(denoise, scaled, adap_mask)

darken = haf.FastLineDarkenMOD(denoise, strength=20, protection=10)
cwarp = xvs.WarpFixChromaBlend(darken, thresh=96, depth=8)
cwarp = core.std.MaskedMerge(cwarp, darken, depth(lmask, 16))


den = mvf.BM3D(cwarp, sigma=6)
diff_den = core.std.MakeDiff(cwarp, den)

detail_mask = lvf.mask.detail_mask(cwarp, sigma=0.7, brz_a=0.012, brz_b=0.015)
deband = dbs.f3kpf(den, range=12, y=80, cb=72, cr=72)
deband = core.std.MaskedMerge(deband, den, detail_mask)
deband = core.std.MergeDiff(deband, diff_den)

grain = kgf.adaptive_grain(deband, 0.45, luma_scaling=0.5)


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
