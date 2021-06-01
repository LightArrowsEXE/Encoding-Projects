import ntpath
import os
from glob import glob

import debandshit as dbs
import havsfunc as haf
import kagefunc as kgf
import lvsfunc as lvf
import vapoursynth as vs
import vardefunc as vdf
import xvs
from finedehalo import fine_dehalo
from vsutil import depth, get_w, get_y, join, plane

core = vs.core


shader = 'FSRCNNX_x2_56-16-4-1.glsl'
if os.path.exists(shader) is False:
    hookpath = r"mpv/shaders/FSRCNNX_x2_56-16-4-1.glsl"
    shader = os.path.join(os.getenv("APPDATA"), hookpath)


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
descale_args = dict(width=get_w(844), height=844)
bicubic_args = dict(b=0, c=1/2)


src = lvf.src(glob(f'{ntpath.basename(__file__)[-6:-4]}/*.mkv')[0])
src8 = src
src16 = depth(src, 16)
src = depth(src, 32)

descaled = core.descale.Debicubic(plane(src, 0), **bicubic_args, **descale_args)
descaled_m = lvf.scale.descale(plane(src, 0), show_mask=True, kernel=lvf.kernels.Bicubic(**bicubic_args), **descale_args)  # noqa
descaled = depth(descaled, 16)

ref = haf.SMDegrain(descaled, tr=1, thSAD=150, prefilter=3, search=3, contrasharp=True, RefineMotion=True)
denoise = lvf.denoise.bm3d(descaled, sigma=0.5, radius=1, ref=ref)

aa = lvf.aa.upscaled_sraa(denoise, rfactor=1.8)
csharp = haf.ContraSharpening(aa, denoise, radius=3, rep=17)

sharp = haf.LSFmod(get_y(csharp), strength=100, soft=10, edgemode=1, Smethod=2, Lmode=2, defaults='slow', edgemaskHQ=True)
sharp = core.std.MaskedMerge(get_y(csharp), sharp, c_mask(csharp))

dehalo = fine_dehalo(sharp, ref=get_y(csharp), rx=4, darkstr=0)

darken = haf.FastLineDarkenMOD(dehalo, strength=16)
rescale = vdf.scale.fsrcnnx_upscale(darken, shader_file=shader)

cwarp = xvs.WarpFixChromaBlend(src, thresh=10)
cwarp = core.std.MaskedMerge(cwarp, src, c_mask(src))
cwarp = depth(cwarp, 16)
cwarp = join([rescale, plane(cwarp, 1), plane(cwarp, 2)])

merged = core.std.MaskedMerge(cwarp, depth(src, 16), depth(descaled_m, 16))

detail_mask = core.std.Expr(
    [lvf.mask.detail_mask(merged,
     sigma=0.4, brz_a=0.0125, brz_b=0.025),
     makemask(plane(merged, 0))],
    expr="x y + abs"
)
deband = dbs.f3kpf(merged, radius=16, threshold=[40, 32])
deband = core.std.MaskedMerge(deband, merged, detail_mask)

grain = kgf.adaptive_grain(deband, 0.2, luma_scaling=4)


out = grain
final = depth(out, 10)
final.set_output(0)


if __name__ == '__vapoursynth__':
    def keyframes(clip: vs.VideoNode, kf_path: str):
        if not os.path.isdir("keyframes"):
            os.makedirs("keyframes")
        kgf.generate_keyframes(clip, out_path=kf_path, header=False)

    kf_path = f"keyframes/{ntpath.basename(__file__)[:-4]}_keyframes.txt"
    if not os.path.isfile(kf_path):
        keyframes(src, kf_path)
