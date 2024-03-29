import os
from pathlib import Path
from typing import Tuple, Union

import vapoursynth as vs
from lvsfunc.misc import source
from vardautomation import FileInfo, PresetBD, PresetFLAC, VPath

from project_module import enc, flt

core = vs.core


shader_file = Path(r'assets/FSRCNNX_x2_56-16-4-1.glsl')
if not shader_file.exists:
    hookpath = r"mpv/shaders/FSRCNNX_x2_56-16-4-1.glsl"
    shader_file = os.path.join(os.getenv("APPDATA"), hookpath)


# Sources
JP_BD = FileInfo(r'E:/src/あっちこっち/[BDMV][121003][Acchi Kocchi][Vol.05]/ACKC_5/BDMV/STREAM/00004.m2ts',
                 [(None, -48)], idx=lambda x: source(x, force_lsmas=True, cachedir=''), preset=[PresetBD, PresetFLAC])
JP_BD.name_file_final = VPath(f"premux/{JP_BD.name} (Premux).mkv")
JP_BD.a_src_cut = VPath(JP_BD.name)
JP_BD.do_qpfile = True


def filterchain() -> Union[vs.VideoNode, Tuple[vs.VideoNode, ...]]:
    """Main VapourSynth filterchain"""
    import debandshit as dbs
    import havsfunc as haf
    import lvsfunc as lvf
    import vardefunc as vdf
    from ccd import ccd
    from muvsfunc import SSIM_downsample
    from vsutil import depth, get_w, get_y

    src = JP_BD.clip_cut
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

    return grain


if __name__ == '__main__':
    FILTERED = filterchain()
    enc.Encoder(JP_BD, FILTERED).run(clean_up=True, aac=False)
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
