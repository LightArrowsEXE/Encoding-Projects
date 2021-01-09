import ntpath
import os
from glob import glob

import adjust
import debandshit as dbs
import havsfunc as haf
import kagefunc as kgf
import lvsfunc as lvf
import mvsfunc as mvf
import vapoursynth as vs
import vardefunc as vdf
import xvs
from finedehalo import fine_dehalo
from vsutil import depth, get_y, iterate, join, plane, scale_value

core = vs.core


shader = 'FSRCNNX_x2_56-16-4-1.glsl'
if os.path.exists(shader) is False:
    hookpath = r"mpv\shaders\FSRCNNX_x2_56-16-4-1.glsl"
    shader = os.path.join(os.getenv("APPDATA"), hookpath)


def brz_aa(clip: vs.VideoNode, opencl: bool = False) -> vs.VideoNode:
    aa = core.eedi3m.EEDI3(clip, field=0, gamma=70)
    diff = core.std.MakeDiff(clip, aa)
    brz = core.std.Binarize(get_y(diff), scale_value(131.5, 8, clip.format.bits_per_sample))
    brz = iterate(brz, core.std.Inflate, 8)
    brz = iterate(brz, core.std.Maximum, 8)
    return core.std.MaskedMerge(aa, lvf.sraa(clip, rep=13), brz)


def keyframes(clip: vs.VideoNode, kf_path: str):
    if os.path.isdir("keyframes") is False:
        os.makedirs("keyframes")
    kgf.generate_keyframes(clip, out_path=kf_path, header=False)


def makemask(clip_y: vs.VideoNode,
             thr: float = (1/10)) -> vs.VideoNode:
    blur = clip_y.std.BoxBlur(hradius=3, vradius=3)
    dark = core.std.Expr([blur, clip_y], 'x y -').std.Binarize(170)
    clean = dark.rgvs.RemoveGrain(3).std.Median()
    dark = core.misc.Hysteresis(clean, dark)
    dev = dark.std.BoxBlur(hradius=8, vradius=8).std.Binarize(65536 * thr)
    return core.std.Expr([dark, dev], 'x y min')


def c_mask(clip: vs.VideoNode) -> vs.VideoNode:
    return core.std.Sobel(get_y(clip)).std.Binarize(75 << 8).std.Minimum()


# Common args
descale_args = dict(height=844, kernel=lvf.kernels.Bicubic(0, 1/2))

# First frame of first cut of the ED
edstart = 31800

# Scenefiltering
undim_ranges = [(edstart+1550, edstart+1579), (edstart+1700, edstart+1817)]
undim_values = [1.3, 1.12]


src = lvf.src(glob(f'{ntpath.basename(__file__)[-6:-4]}/*.mkv')[0])
t = src
for value, ranges in zip(undim_values, undim_ranges):
    undim = adjust.Tweak(src, sat=value, cont=value)
    src = lvf.rfs(src, undim, [ranges])
src = depth(src, 32)

descaled = lvf.scale.descale(src, upscaler=None, **descale_args)
descaled_m = lvf.scale.descale(src, show_mask=True, **descale_args)
descaled = depth(descaled, 16)

ref = haf.SMDegrain(descaled, tr=1, thSAD=150, prefilter=3, search=3, contrasharp=True, RefineMotion=True)
denoise = mvf.BM3D(descaled, sigma=0.75, radius1=1, profile1='lc', psample=0, ref=ref)

aa = brz_aa(denoise)

sharp = haf.LSFmod(get_y(aa), strength=80, soft=10, edgemode=1, Smethod=2, Lmode=2, defaults='slow', edgemaskHQ=True)
sharp = core.std.MaskedMerge(get_y(aa), sharp, c_mask(aa))

dehalo = fine_dehalo(sharp, ref=get_y(aa), rx=4, darkstr=0)

darken = haf.FastLineDarkenMOD(dehalo, strength=12)
rescale = vdf.fsrcnnx_upscale(darken, shader_file=shader)

cwarp = xvs.WarpFixChromaBlend(src, thresh=10)
cwarp = core.std.MaskedMerge(cwarp, src, c_mask(src))
cwarp = depth(cwarp, 16)
cwarp = join([rescale, plane(cwarp, 1), plane(cwarp, 2)])

merged = core.std.MaskedMerge(cwarp, depth(src, 16), depth(descaled_m, 16))

detail_mask = core.std.Expr(
    [lvf.denoise.detail_mask(merged,
     sigma=0.7, brz_a=0.0125, brz_b=0.025),
     makemask(plane(merged, 0))],
     expr="x y + abs")
deband = dbs.f3kpf(merged, range=16, y=40, cb=32)
deband = core.std.MaskedMerge(deband, merged, detail_mask)

grain = kgf.adaptive_grain(deband, 0.2, luma_scaling=4)


out = grain
final = depth(out, 10)
final.set_output()


if __name__ == '__vapoursynth__':
    kf_path = f"keyframes/{ntpath.basename(__file__)[:-4]}_keyframes.txt"
    if os.path.isfile(kf_path) is False:
        print("Keyframe file not found; generating")
        keyframes(src, kf_path)
