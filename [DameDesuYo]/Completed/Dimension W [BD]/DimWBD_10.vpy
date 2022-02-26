import ntpath
import os

import adptvgrnMod as adm
import awsmfunc as awsm
import debandshit as dbs
import havsfunc as haf
import kagefunc as kgf
import lvsfunc as lvf
import mvsfunc as mvf
import vapoursynth as vs
import vardefunc as vdf
from vsutil import depth, get_y, iterate, join, plane, split

core = vs.core

shader = 'FSRCNNX_x2_56-16-4-1.glsl'
if os.path.exists(shader) is False:
    hookpath = r"mpv\shaders\FSRCNNX_x2_56-16-4-1.glsl"
    shader = os.path.join(os.getenv("APPDATA"), hookpath)


def denoising(clip: vs.VideoNode) -> vs.VideoNode:
    # There is heavy starved grain over the entire clip, so this is stronger than usual
    ref = haf.SMDegrain(clip, tr=1, thSAD=225, prefilter=3, search=3, contrasharp=True, RefineMotion=True)
    return mvf.BM3D(clip, sigma=1.3, profile1='lc', psample=0, ref=ref)


def makemask(clip_y: vs.VideoNode,
             thr: float = (1/10)) -> vs.VideoNode:
    blur = clip_y.std.BoxBlur(hradius=3, vradius=3)
    dark = core.std.Expr([blur, clip_y], 'x y -').std.Binarize(170)
    clean = dark.rgvs.RemoveGrain(3).std.Median()
    dark = core.misc.Hysteresis(clean, dark)
    dev = dark.std.BoxBlur(hradius=8, vradius=8).std.Binarize(65536 * thr)
    return core.std.Expr([dark, dev], 'x y min')


def blur(clip: vs.VideoNode, sigma: float = 1) -> vs.VideoNode:
    return core.bilateral.Gaussian(clip, sigma=sigma)


# Arguments that will differ between 720p and 1080p
deband_args = dict(range=14, y=24, cb=24)
dehalo_mask_args = dict(sigma=1.5, edgemasking=lambda clip, sigma: kgf.retinex_edgemask(clip, sigma=sigma))
ef_args = dict(top=3, bottom=3, left=3, right=3)
scale_args = dict(kernel=lvf.kernels.Bicubic(0, 1))


# `--arg` passed through vspipe (see ``settings.sh``)
try:
    enc_1080  # noqa
    upscaled = True
    deband_args.update(range=16, y=32, cb=32)
except NameError:
    upscaled = False


# Some defaults
offset = 0

# OP/ED filtering. First frame
opstart = 815
edstart = 32511

op_offset = 1
ed_offset = 1


src = lvf.src(r"BDMV/DIMENSION_W_5/FullDisc/DIMENSION_W_5/BDMV/STREAM/00008.m2ts")[:-24]
ef = awsm.bbmod(src, **ef_args)
b = core.std.BlankClip(ef, length=1)

if opstart is not False:
    src_NCOP = lvf.src(r"BDMV/DIMENSION_W_4/FullDisc/DIMENSION_W_4/BDMV/STREAM/00013.m2ts")[:-24-op_offset]
    blurred_src_NCOP = blur(src_NCOP)
    op_scomp = lvf.scomp(src[opstart:opstart+src_NCOP.num_frames-1]+b, src_NCOP+b, make_diff=True)
if edstart is not False:
    src_NCED = lvf.src(r"BDMV/DIMENSION_W_1/BDMV/STREAM/00013.m2ts")[275:-24-ed_offset]
    ef_NCED = awsm.bbmod(src_NCED, **ef_args)
    blurred_ef_NCED = blur(ef_NCED, sigma=1.1)
    ed_scomp = lvf.scomp(src[edstart:edstart+src_NCED.num_frames-1-op_offset]+b, src_NCED+b, make_diff=True)


# Masking credits
blurred_src = blur(src)
blurred_ef = blur(ef)
op_mask = vdf.diff_creditless_mask(blurred_src, blurred_src[opstart:opstart+src_NCOP.num_frames-1],
                                   blurred_src_NCOP, opstart, opstart+src_NCOP.num_frames-1) \
                                   if opstart is not False else get_y(core.std.BlankClip(src))
ed_mask = vdf.diff_creditless_mask(ef, blurred_ef[edstart:edstart+src_NCED.num_frames-1],
                                   blurred_ef_NCED, edstart, edstart+src_NCED.num_frames-1) \
                                   if edstart is not False else get_y(core.std.BlankClip(src))
descale_mask = depth(lvf.scale.descale(src, show_mask=True, **scale_args), 8)
credit_mask = core.std.Expr([op_mask, ed_mask, descale_mask], expr='x y + z +')
credit_mask = iterate(credit_mask, core.std.Maximum, 3)
credit_mask = depth(credit_mask, 16).std.Binarize()
cm_scomp = lvf.scomp(src, credit_mask.resize.Bicubic(format=src.format))

ef = depth(ef, 32)

descaled = lvf.scale.descale(ef, upscaler=None, **scale_args)
descaled = depth(descaled, 16)

if upscaled:
    planes = split(depth(ef, 16))
    planes[1], planes[2] = [denoising(p) for p in planes[1:]]

chr = core.resize.Bicubic(ef, descaled.width, descaled.height, format=vs.YUV444P16)
descaled = join([descaled, plane(chr, 1), plane(chr, 2)])
denoise = denoising(descaled)

# Blurring makes for a fine way to get rid of haloing. Rather weak to not kill darker lines, still
dehalo_m = lvf.mask.halo_mask(denoise, **dehalo_mask_args)
blur = core.bilateral.Gaussian(denoise, sigma=0.6)
dehalo = core.std.MaskedMerge(denoise, blur, dehalo_m)

aa = lvf.sraa(denoise, rfactor=2, rep=13, downscaler=lvf.kernels.Bicubic().scale, opencl=True)

if upscaled:
    upscaled = vdf.fsrcnnx_upscale(get_y(aa), ef.width*2, ef.height*2, shader) \
        .resize.Spline36(ef.width, ef.height)
    scaled = join([upscaled, planes[1], planes[2]])
    recon = lvf.recon.chroma_reconstruct(scaled)
else:
    recon = lvf.recon.chroma_reconstruct(aa, i444=True)
    ef = ef.resize.Bicubic(recon.width, recon.height, recon.format)
    credit_mask = credit_mask.resize.Bicubic(recon.width, recon.height)

recon = core.std.MaskedMerge(recon, ef, credit_mask)

detail_mask = core.std.Expr(
    [lvf.mask.detail_mask(recon,
     sigma=0.7, brz_a=0.0125, brz_b=0.025),
     makemask(plane(recon, 0))],
    expr="x y + abs")
deband = dbs.f3kpf(recon, **deband_args)
deband = core.std.MaskedMerge(deband, recon, detail_mask)

# Size relative to output resolution, so should work nicely
grain = adm.adptvgrnMod(deband, strength=.2, size=1.05, luma_scaling=2, grain_chroma=False)


out = grain
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
