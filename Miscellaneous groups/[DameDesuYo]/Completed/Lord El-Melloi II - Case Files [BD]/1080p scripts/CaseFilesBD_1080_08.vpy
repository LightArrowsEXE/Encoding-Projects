import ntpath
import os
import re

import awsmfunc as awsm
import debandshit as dbs
import havsfunc as haf
import kagefunc as kgf
import lvsfunc as lvf
import mvsfunc as mvf
import vapoursynth as vs
import vardefunc as vdf
from finedehalo import fine_dehalo
from vsutil import depth, get_y, join, plane, scale_value

core = vs.core

shader = 'FSRCNNX_x2_56-16-4-1.glsl'
if os.path.exists(shader) is False:
    hookpath = r"mpv\shaders\FSRCNNX_x2_56-16-4-1.glsl"
    shader = os.path.join(os.getenv("APPDATA"), hookpath)


def keyframes(clip: vs.VideoNode, kf_path: str):
    try:
        os.makedirs("keyframes")
    except:
        pass
    kgf.generate_keyframes(clip, out_path=kf_path)


def interp_aa(clip: vs.VideoNode) -> vs.VideoNode:
    l_mask = kgf.retinex_edgemask(clip).std.Maximum()
    b_mask = core.std.Binarize(
        get_y(clip), scale_value(0.3, 32, 16)).std.Invert()
    mask = core.std.Expr([l_mask, b_mask], "x y -").std.Maximum().std.Inflate()

    aa = core.eedi3m.EEDI3(clip, field=1, mclip=mask.resize.Point(format=clip.format))
    return core.std.MaskedMerge(aa, haf.QTGMC(aa, InputType=1, TR2=3), mask)


def makemask(clip_y: vs.VideoNode,
             thr: float = (1/10)) -> vs.VideoNode:
    blur = clip_y.std.BoxBlur(hradius=3, vradius=3)
    dark = core.std.Expr([blur, clip_y], 'x y -').std.Binarize(170)
    clean = dark.rgvs.RemoveGrain(3).std.Median()
    dark = core.misc.Hysteresis(clean, dark)
    dev = dark.std.BoxBlur(hradius=8, vradius=8).std.Binarize(65536 * thr)
    return core.std.Expr([dark, dev], 'x y min')


# Arguments that will differ between 720p and 1080p
upscaled = False
scale_args = dict(upscaler=None)
sharpen_args = dict(strength=40, soft=10, edgemode=1, Smethod=2, Lmode=2, defaults='slow', edgemaskHQ=True)
darken_args = dict(strength=18)

if re.search("1080", ntpath.basename(__file__)):
    upscaled = True
    scale_args.update(upscaler=lvf.scale.reupscale)
    sharpen_args.update(strength=80)
    darken_args.update(strength=24)

# Enable/Disable certain filtering
opstart = 4245
edstart = 31889
edgefix = True  # Most eps need edgefixing, some don't

# Scenefiltering
OP_replace_scene = [(opstart+875, opstart+890)]
OP_dehalo = [(opstart+960, opstart+1028)]
interp_aa_ranges = []


src = lvf.src(r"BDMV/[BDMV][191204][Lord El-Melloi II-sei no Jikenbo][Vol.04]/BDROM/BDMV/STREAM/00001.m2ts")[24:-24]

if opstart is not None:
    src_NCOP = lvf.src(r'BDMV/[BDMV] Lord El-Melloi II-sei no Jikenbo ~Rail Zeppelin Grace Note~ [Vol.02]/BDROM/BDMV/STREAM/00004.m2ts')[24:-24]
if edstart is not None:
    src_NCED = lvf.src(r'BDMV/[BDMV] Lord El-Melloi II-sei no Jikenbo ~Rail Zeppelin Grace Note~ [Vol.02]/BDROM/BDMV/STREAM/00005.m2ts')[24:-41]

b = core.std.BlankClip(src).std.Invert()
src = lvf.rfs(src, b[:opstart]+src_NCOP, OP_replace_scene) if opstart else src
ef = awsm.bbmod(src, 1, 1, 1, 1) if edgefix else src
ef = depth(ef, 32)


kf_path = f"keyframes/{ntpath.basename(__file__)[:-4]}_keyframes.txt"
if os.path.isfile(kf_path) is False:
    print("Keyframe file not found; generating")
    keyframes(ef, kf_path)


op_mask = vdf.diff_creditless_mask(src, src[opstart:opstart+src_NCOP.num_frames-1],
    src_NCOP, opstart, opstart+src_NCOP.num_frames-1) \
    if opstart else get_y(core.std.BlankClip(src))
ed_mask = vdf.diff_creditless_mask(src, src[edstart:edstart+src_NCED.num_frames-1],
    src_NCED, edstart, edstart+src_NCED.num_frames-1) \
    if edstart else get_y(core.std.BlankClip(src))
credit_mask = core.std.Expr([op_mask, ed_mask], expr='x y +')
credit_mask = depth(credit_mask, 16) if upscaled \
    else credit_mask.resize.Bicubic(1280, 720, vs.GRAY16)


descaled = lvf.scale.descale(ef, upscaler=None)
if upscaled:
    upscaled = vdf.fsrcnnx_upscale(descaled, shader_file=shader)
    scaled = join([upscaled, plane(ef, 1), plane(ef, 2)])
else:
    chr = core.resize.Bicubic(ef, descaled.width, descaled.height, vs.YUV444PS)
    scaled = join([descaled, plane(chr, 1), plane(chr, 2)])
descale_mask = lvf.scale.descale(ef, show_mask=True, **scale_args)
credit_mask = core.std.Expr([credit_mask, depth(descale_mask, 16)], "x y + abs")
scaled = depth(scaled, 16)

ref = haf.SMDegrain(scaled, tr=1, thSAD=150, prefilter=3, search=3, contrasharp=True, RefineMotion=True)
denoise = mvf.BM3D(scaled, sigma=[1, 1.25], radius1=1, profile1='lc', psample=0, ref=ref)


aa = lvf.rfs(denoise, interp_aa(denoise), interp_aa_ranges)

sharp = haf.LSFmod(get_y(aa), **sharpen_args)
lmask = core.std.Sobel(get_y(aa)).std.Binarize(75 << 8).std.Minimum()
sharp = core.std.MaskedMerge(get_y(aa), sharp, lmask)

dehalo_main = fine_dehalo(sharp, ref=get_y(aa))
dehalo_strong = fine_dehalo(sharp, rx=2.8, brightstr=1.2, darkstr=0)
dehalo = lvf.rfs(dehalo_main, dehalo_strong, OP_dehalo)

darken = haf.FastLineDarkenMOD(dehalo, **darken_args)
darken = join([darken, plane(aa, 1), plane(aa, 2)])


chr = depth(ef, 16) if upscaled else depth(chr, 16)
merged = core.std.MaskedMerge(darken, chr, credit_mask)


diff_den = mvf.BM3D(darken, sigma=[2.5,0], profile1='lc')
diff_clip = core.std.MakeDiff(darken, diff_den)

detail_mask = core.std.Expr(
    [lvf.denoise.detail_mask(merged,
     sigma=0.7, brz_a=0.0125, brz_b=0.025),
     makemask(plane(merged, 0))],
     expr="x y + abs")
deband = dbs.f3kpf(diff_den, range=16, y=32, cb=24)
deband = core.std.MaskedMerge(deband, diff_den, detail_mask)
diff_rev = core.std.MergeDiff(deband, diff_clip)

grain = kgf.adaptive_grain(diff_rev, 0.1, luma_scaling=4)


out = grain
final = depth(out, 10)
final.set_output()
