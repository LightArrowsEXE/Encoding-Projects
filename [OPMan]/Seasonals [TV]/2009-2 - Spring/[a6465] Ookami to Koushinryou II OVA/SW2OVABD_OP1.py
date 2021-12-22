import os
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union
import awsmfunc

import vapoursynth as vs
from lvsfunc.misc import source
from lvsfunc.types import Range
from vardautomation import FileInfo, PresetBD, PresetFLAC, VPath

from project_module import enc, flt

core = vs.core


shader_file = 'assets/FSRCNNX_x2_16-0-4-1.glsl'
if not Path(shader_file).exists():
    hookpath = r"mpv/shaders/FSRCNNX_x2_16-0-4-1.glsl"
    shader_file = os.path.join(str(os.getenv("APPDATA")), hookpath)


# Sources
JP_BD = FileInfo(r"E:/src/[BDMV] Spice and Wolf Blu-ray BOX Complete Edition R2J/[BDMV][130306] Spice and Wolf Disc5/BDMV/STREAM/00001.m2ts",  # noqa
                 [(None, -24)], idx=lambda x: source(x, force_lsmas=True, cachedir=''), preset=[PresetBD, PresetFLAC])
JP_BD.name_file_final = VPath(f"premux/{JP_BD.name} (Premux).mkv")
JP_BD.a_src_cut = VPath(JP_BD.name)
JP_BD.do_qpfile = True


strong_debanding: List[Range] = [  # Ranges for stronger debanding
]

zones: Dict[Tuple[int, int], Dict[str, Any]] = {  # Zoning for the encoder
}


def filterchain() -> Union[vs.VideoNode, Tuple[vs.VideoNode, ...]]:
    """Main VapourSynth filterchain"""
    import debandshit as dbs
    import havsfunc as haf
    import lvsfunc as lvf
    import rekt
    import vardefunc as vdf
    from awsmfunc import bbmod
    from ccd import ccd
    from muvsfunc import SSIM_downsample
    from vsutil import depth, get_w, get_y

    src = JP_BD.clip_cut
    src = depth(src, 16)

    rkt_a = rekt.rektlvls(src, [0, -1], [15, 15], [0, 1, 2, 3, -6, -4, -3, -2, -1], [13, 3, -1, 1, -1, 1, -2, 4, 11])
    rkt_b = rekt.rektlvls(src, [0, 1, -2, -1], [12, -11, -11, 12], [0, 1, -2, -1], [12, -11, -11, 12])
    bb_b = bbmod(rkt_b, 2, 2, 2, 2, blur=50, y=False)
    rkt = lvf.rfs(rkt_a, bb_b, [(2496, 2567)])
    rkt = lvf.rfs(rkt, src, [(1589, 1660), (1733, 1800), (1873, 1943), (2016, 2046), (2119, 2141), (2214, 2279)])

    ef = depth(rkt, 32)
    src_y = get_y(ef)

    pre_den = core.dfttest.DFTTest(src_y, sigma=3.0)
    l_mask = vdf.mask.FDOG().get_mask(pre_den, lthr=0.125, hthr=0.050).rgsf.RemoveGrain(4).rgsf.RemoveGrain(4)
    l_mask = l_mask.std.Minimum().std.Deflate().std.Median().std.Convolution([1] * 9).std.Maximum()

    # Descaling.
    descaled = lvf.kernels.Catrom().descale(src_y, get_w(720, src_y.width/src_y.height), 720)
    descaled = core.resize.Bicubic(descaled, format=vs.YUV444P16)

    # Slight AA in an attempt to forcibly fix starved lineart.
    baa = lvf.aa.based_aa(descaled, shader_file)
    sraa = lvf.aa.upscaled_sraa(descaled, rfactor=1.45)
    clamp_aa = lvf.aa.clamp_aa(descaled, baa, sraa, strength=1.15)
    clamp_aa = depth(get_y(clamp_aa), 32)

    # Doing a mixed reupscale using nn3/fsrcnnx, grabbing the darkest parts of each
    rescaled_nn3 = vdf.scale.nnedi3cl_double(clamp_aa, use_znedi=True, pscrn=1)
    rescaled_fsrcnnx = vdf.scale.fsrcnnx_upscale(clamp_aa, rescaled_nn3.width, rescaled_nn3.height, shader_file)
    rescaled = core.std.Expr([rescaled_nn3, rescaled_fsrcnnx], "x y min")

    downscaled = SSIM_downsample(rescaled, src_y.width, src_y.height, smooth=((3 ** 2 - 1) / 12) ** 0.5,
                                 sigmoid=True, filter_param_a=-1/2, filter_param_b=1/4)
    downscaled = core.std.MaskedMerge(src_y, downscaled, l_mask)

    scaled = depth(vdf.misc.merge_chroma(downscaled, ef), 16)

    # Clean frame for credit masking and/or NC creation purposes
    clean = lvf.src(r'assets/OP1/SW2OVABD_OP1_clean_canvas.png', ref=scaled)
    clean = lvf.rfs(scaled, clean, [(None, 71), (168, 239), (336, 407), (475, 546), (612, 683), (780, 851),
                                    (948, 1019), (1164, 1235), (1302, 1373), (1518, 1589), (1661, 1732),
                                    (1801, 1872), (1944, 2015), (2047, 2118), (2142, 2213), (2280, 2351),
                                    (2424, 2495), (2568, 2639), (2712, 2783)])

    # Chroma warping to forcibly wrap it a bit nicer around the lineart. Also fixing slight shift. 4:2:0 was a mistake.
    cwarp = clean.warp.AWarpSharp2(thresh=72, blur=3, type=1, depth=6, planes=[1, 2])

    # The textures and detail are very smeary, so gotta be careful not to make it even worse
    stab = haf.GSMC(cwarp, radius=3, planes=[0], thSAD=75)
    den_uv = ccd(stab, threshold=5, matrix='709')
    decs = vdf.noise.decsiz(den_uv, sigmaS=8.0, min_in=200 << 8, max_in=240 << 8)

    # Scenefiltered debanding. Not graining, since we kept most of the original grain anyway.
    deband_wk = dbs.debanders.dumb3kdb(decs, radius=16, threshold=[28, 0], grain=0)
    deband_wk = core.placebo.Deband(deband_wk, iterations=2, threshold=3.5, radius=12, grain=0, planes=2 | 4)

    # Strong denoising + debanding to hopefully deal with all the awful bands. Courtesy of :b:arde
    dft = core.dfttest.DFTTest(decs, sigma=4.0)
    ccd_uv = ccd(dft, threshold=10, matrix='709')
    f3k = dbs.debanders.dumb3kdb(ccd_uv, radius=8, threshold=[36, 24], grain=0)
    plac = flt.masked_placebo(f3k, rad=18, thr=5.5, itr=2, grain=3.0,
                              mask_args={'detail_brz': 100, 'lines_brz': 450})

    dft_diff = core.std.MakeDiff(decs, dft)
    plac_diff = core.std.MergeDiff(plac, dft_diff)

    deband = lvf.rfs(deband_wk, plac_diff, strong_debanding)

    return deband


if __name__ == '__main__':
    FILTERED = filterchain()
    enc.Encoder(JP_BD, FILTERED).run(clean_up=True, settings_name='x265_settings', zones=zones)
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
