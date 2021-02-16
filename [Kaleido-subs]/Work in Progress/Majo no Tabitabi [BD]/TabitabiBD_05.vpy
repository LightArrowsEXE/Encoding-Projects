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
opstart = 1176
edstart = 31242

op_offset = 2
ed_offset = 2

# Sometimes I can't mask the credits nicely with automations
credit_mask_ranges = [(3514, 3620)]

# Not do any scaling (and by extension AA/Dehalo) on these ranges
noscale_ranges = []


src = lvf.src(r"BDMV/[BDMV][アニメ][210127][MAJO_NO_TABITABI_1][Blu-Ray BOX 上]/BDMV/STREAM/00012.m2ts")[24:-24]
b = core.std.BlankClip(src, length=1)

if opstart is not False:
    src_NCOP = lvf.src(r"BDMV/[BDMV][アニメ][210127][MAJO_NO_TABITABI_1][Blu-Ray BOX 上]/BDMV/STREAM/00007.m2ts")[24:-24]
    op_scomp = lvf.scomp(src[opstart:opstart+src_NCOP.num_frames-1-op_offset]+b, src_NCOP[:-op_offset]+b, make_diff=True)
if edstart is not False:
    src_NCED = lvf.src(r"BDMV/[BDMV][アニメ][210127][MAJO_NO_TABITABI_1][Blu-Ray BOX 上]/BDMV/STREAM/00016.m2ts")[24:-24]
    ed_scomp = lvf.scomp(src[edstart:edstart+src_NCED.num_frames-1-ed_offset]+b, src_NCED[:-ed_offset]+b, make_diff=True)


# Masking credits
op_mask = vdf.diff_creditless_mask(src, src[opstart:opstart+src_NCOP.num_frames-1-op_offset],
                                   src_NCOP[:-op_offset], opstart, opstart+src_NCOP.num_frames-1-op_offset) \
                                   if opstart is not False else get_y(core.std.BlankClip(src))
ed_mask = vdf.diff_creditless_mask(src, src[edstart:edstart+src_NCED.num_frames-1-ed_offset],
                                   src_NCED[:-ed_offset], edstart, edstart+src_NCED.num_frames-1-ed_offset) \
                                   if edstart is not False else get_y(core.std.BlankClip(src))
descale_mask = depth(lvf.scale.descale(src, show_mask=True, **scale_args), 8)
credit_mask = core.std.Expr([op_mask, ed_mask, descale_mask], expr='x y + z +')
credit_mask = iterate(credit_mask, core.std.Maximum, 3)
credit_mask = depth(credit_mask, 16).std.Binarize()

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

org = depth(ef, 16)
merge = core.std.MaskedMerge(cwarp, org, credit_mask)

if credit_mask_ranges:
    ranged_masks = [read_credit_mask(i, f, merge) for i, f in enumerate(credit_mask_ranges, 1)]

    for ranges, mask in ranged_masks:
        mask = iterate(mask, core.std.Maximum, 2)
        mask = core.std.Expr([credit_mask, get_y(mask)], expr='x y +')
        credit_masked = core.std.MaskedMerge(merge, org, mask)
        merge = lvf.rfs(merge, credit_masked, ranges)

den = mvf.BM3D(merge, sigma=6)
diff_den = core.std.MakeDiff(merge, den)

detail_mask = lvf.mask.detail_mask(merge, sigma=0.7, brz_a=0.012, brz_b=0.015)
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
