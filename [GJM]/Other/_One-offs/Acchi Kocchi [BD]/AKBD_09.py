import os
from functools import partial
from pathlib import Path
from typing import Tuple, Union

import vapoursynth as vs
from lvsfunc.misc import source
from vardautomation import FileInfo, PresetAAC, PresetBD, VPath

from project_module import enc, flt

core = vs.core


shader_file = Path(r'assets/FSRCNNX_x2_56-16-4-1.glsl')
if not shader_file.exists:
    hookpath = r"mpv/shaders/FSRCNNX_x2_56-16-4-1.glsl"
    shader_file = os.path.join(os.getenv("APPDATA"), hookpath)


# Sources
JP_BD = FileInfo(r'E:/src/[BDMV][121003][Acchi Kocchi][Vol.05]/ACKC_5/BDMV/STREAM/00000.m2ts', [(None, -48)],
                 idx=lambda x: source(x, force_lsmas=True, cachedir=''), preset=[PresetBD, PresetAAC])
JP_NCOP = FileInfo(r'E:/src/あっちこっち/[BDMV][121003][Acchi Kocchi][Vol.05]/ACKC_5/BDMV/STREAM/00004.m2ts',
                   [(None, -48)], idx=lambda x: source(x, force_lsmas=True, cachedir=''))
JP_NCED = FileInfo(r'E:/src/あっちこっち/[BDMV][121003][Acchi Kocchi][Vol.05]/ACKC_5/BDMV/STREAM/00008.m2ts',
                   [(None, -48)], idx=lambda x: source(x, force_lsmas=True, cachedir=''))
JP_BD.name_file_final = VPath(f"premux/{JP_BD.name} (Premux).mkv")
JP_BD.a_src_cut = VPath(JP_BD.name)
JP_BD.do_qpfile = True


# OP/ED scenefiltering
opstart = 888
edstart = 31920
op_offset = 1
ed_offset = 1


def filterchain() -> Union[vs.VideoNode, Tuple[vs.VideoNode, ...]]:
    """Main VapourSynth filterchain"""
    import debandshit as dbs
    import havsfunc as haf
    import lvsfunc as lvf
    import vardefunc as vdf
    from ccd import ccd
    from muvsfunc import SSIM_downsample
    from vsutil import depth, get_w, get_y, insert_clip

    src = JP_BD.clip_cut
    src_c = src
    src_ncop, src_nced = JP_NCOP.clip_cut, JP_NCED.clip_cut
    b = core.std.BlankClip(src, length=1)

    # OP/ED stack comps to check if they line up
    if opstart is not False:
        op_scomp = lvf.scomp(src[opstart:opstart+src_ncop.num_frames-1]+b, src_ncop[:-op_offset]+b) \
            .text.Text('src', 7).text.Text('op', 9)
    if edstart is not False:
        ed_scomp = lvf.scomp(src[edstart:edstart+src_nced.num_frames-1]+b, src_nced[:-ed_offset]+b) \
            .text.Text('src', 7).text.Text('ed', 9)

    # Splicing in NCs and diff'ing back the credits
    if opstart is not False:
        src = insert_clip(src, src_ncop[:-op_offset], opstart)
        src = lvf.rfs(src, src_c, [(opstart+811, opstart+859)])
    if edstart is not False:
        src = insert_clip(src, src_nced[:-ed_offset], edstart)

    den_src, den_ncs = map(partial(core.dfttest.DFTTest, sigma=10), [src_c, src])
    den_src, den_ncs = depth(den_src, 32), depth(den_ncs, 32)
    diff = core.std.MakeDiff(den_src, den_ncs).dfttest.DFTTest(sigma=50.0)

    # For some reason there's noise from previous credits remaining? Removing that here
    diff_brz = vdf.misc.merge_chroma(diff.std.Binarize(0.03), diff)
    diff = core.std.Expr([diff, diff_brz], "x y min")

    src = depth(src, 16)

    # We're pre-denoising here, as the kernel is very sharp and the dither was added after scaling
    sqmask = lvf.mask.BoundingBox((1, 1), (src.width-2, src.height-2)).get_mask(src)
    adap = core.adg.Mask(src.std.PlaneStats(), 8)

    den_y = haf.SMDegrain(src, tr=1, thSAD=75, plane=0, contrasharp=True)

    den_y_dark = core.dfttest.DFTTest(den_y, sigma=0.75)
    den_y_bright = core.dfttest.DFTTest(den_y, sigma=4.6)
    den_y = core.std.MaskedMerge(den_y_bright, den_y_dark, adap)

    den_y = core.std.MaskedMerge(src, den_y, sqmask)
    den_uv = ccd(den_y, threshold=4, matrix='709')

    decs = vdf.noise.decsiz(den_uv, sigmaS=3.0, min_in=216 << 8, max_in=240 << 8)
    decs = depth(decs, 32)

    # Rescaling
    clip_y = get_y(decs)

    l_mask = vdf.mask.FDOG().get_mask(clip_y, lthr=0.115, hthr=0.115).rgsf.RemoveGrain(4).rgsf.RemoveGrain(4)
    l_mask = l_mask.std.Minimum().std.Deflate().std.Median().std.Convolution([1] * 9).std.Maximum()

    descaled = lvf.kernels.RobidouxSoft().descale(clip_y, get_w(720), 720)
    double = vdf.scale.nnedi3cl_double(descaled, use_znedi=True, pscrn=1)
    downscale = SSIM_downsample(double, src.width, src.height, smooth=((3 ** 2 - 1) / 12) ** 0.5,
                                sigmoid=True, filter_param_a=-1/2, filter_param_b=1/4)
    masked = core.std.MaskedMerge(clip_y, downscale, l_mask)
    scaled = depth(vdf.misc.merge_chroma(masked, decs), 16)

    # Slight chromawarping and brightening. Robidoux soft is super blurry, so the result is super sharp and too dark
    cwarp = scaled.warp.AWarpSharp2(thresh=96, blur=3, type=1, depth=5, planes=[1, 2])
    brighten = haf.FastLineDarkenMOD(cwarp, strength=-12)

    deband = core.average.Mean([
        dbs.debanders.dumb3kdb(brighten, radius=18, threshold=[32, 24], grain=[12, 6]),
        flt.masked_placebo(brighten, rad=20, thr=5.5, itr=2, grain=1, mask_args={'detail_brz': 250, 'lines_brz': 650}),
    ])

    grain = vdf.noise.Graigasm(
        thrs=[x << 8 for x in (32, 80, 128, 176)],
        strengths=[(0.15, 0.0), (0.10, 0.0), (0.05, 0.0), (0.0, 0.0)],
        sizes=(1.15, 1.10, 1.05, 1),
        sharps=(80, 70, 60, 50),
        grainers=[
            vdf.noise.AddGrain(seed=69420, constant=False),
            vdf.noise.AddGrain(seed=69420, constant=False),
            vdf.noise.AddGrain(seed=69420, constant=False)
        ]).graining(deband)

    merge_creds = core.std.MergeDiff(depth(grain, 32), diff)

    # Masking native 1080p text scroll at the end. I hate this, but it worksTM
    src32 = depth(src, 32)
    crop_src = core.std.CropRel(src32, top=936)
    crop_final = core.std.CropRel(merge_creds, top=936)

    clean_src = crop_src[34792] * (crop_src.num_frames - 1)
    clean_final = crop_final[34792] * (crop_final.num_frames - 1)

    diff = core.std.MakeDiff(crop_src, clean_src).dfttest.DFTTest(sigma=50.0)
    aa = lvf.aa.upscaled_sraa(diff, rfactor=1.75)
    darken = haf.FastLineDarkenMOD(aa, strength=24)
    merge_diff = core.std.MergeDiff(clean_final, darken)

    stack = core.std.StackVertical([merge_creds.std.CropRel(bottom=144), merge_diff])
    ins_clean = lvf.rfs(merge_creds, stack, [(34206, None)])

    return ins_clean


if __name__ == '__main__':
    FILTERED = filterchain()
    enc.Encoder(JP_BD, FILTERED).run(clean_up=True)
elif __name__ == '__vapoursynth__':
    FILTERED = filterchain()
    if not isinstance(FILTERED, vs.VideoNode):
        raise ImportError(
            f"Input clip has multiple output nodes ({len(FILTERED)})! Please output a single clip")
    else:
        enc.dither_down(FILTERED).set_output(0)
else:
    JP_BD.clip_cut.std.SetFrameProp('node', intval=0).set_output(0)
    FILTERED = filterchain()
    if not isinstance(FILTERED, vs.VideoNode):
        for i, clip_filtered in enumerate(FILTERED, start=1):
            clip_filtered.std.SetFrameProp('node', intval=i).set_output(i)
    else:
        FILTERED.std.SetFrameProp('node', intval=1).set_output(1)
