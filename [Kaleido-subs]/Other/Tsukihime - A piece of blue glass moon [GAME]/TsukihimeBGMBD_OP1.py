import os
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union

import vapoursynth as vs
from lvsfunc.misc import source
from lvsfunc.types import Range
from vardautomation import FileInfo, PresetBD, PresetFLAC, VPath

from project_module import encoder as enc
from project_module import flt

core = vs.core


shader_file = 'assets/FSRCNNX_x2_56-16-4-1.glsl'
if not Path(shader_file).exists():
    hookpath = r"mpv/shaders/FSRCNNX_x2_56-16-4-1.glsl"
    shader_file = os.path.join(os.getenv("APPDATA"), hookpath)


# Sources
JP_BD = FileInfo(r'src/[天使动漫]月姫 -A piece of blue glass moon- THEME SONG E.P.(bdmv)/BDMV/STREAM/00004.m2ts',
                 (None, -48), idx=lambda x: source(x, force_lsmas=True, cachedir=''), preset=[PresetBD, PresetFLAC])
JP_BD.name_file_final = VPath(fr"premux/{JP_BD.name} (Premux).mkv")
JP_BD.do_lossless = True
if Path(JP_BD.name_clip_output_lossless).is_file():
    JP_BD.do_qpfile = True
# Audio Shift: 392ms


strong_aa: List[Range] = [  # Why is ufo lineart so good
    (531, 582), (1619, 1620), (1623, 1626), (1687, 1690), (1693, 1704), (1807, 1810)
]

heavy_grain: List[Range] = [  # Scenes with super heavy grain
]

zones: Dict[Tuple[int, int], Dict[str, Any]] = {  # Zones for x265
    (885, 993): {'b': 1.15},  # Murdered by psy-rd(oq) otherwise
    (1078, 1116): {'b': 1.15},  # Murdered by psy-rd(oq) otherwise
    (1603, 1810): {'b': 1.1},  # Murdered by psy-rd(oq) otherwise
}


def pre_filter() -> vs.VideoNode:
    """Pre-filtering to fix some stuff"""
    from vsutil import insert_clip

    src = JP_BD.clip_cut

    # The grain pattern randomly stops in the middle??? ufo, WHAT
    ins = insert_clip(src, src[877:881], 881)

    return ins


def filterchain() -> Union[vs.VideoNode, Tuple[vs.VideoNode, ...]]:
    """Main filterchain"""
    import EoEfunc as eoe
    import havsfunc as haf
    import kagefunc as kgf
    import lvsfunc as lvf
    import vardefunc as vdf
    from adptvgrnMod import adptvgrnMod
    from ccd import ccd
    from vsdpir import DPIR
    from vsutil import depth

    src = pre_filter()
    src = depth(src, 16)

    # Fix slight green tint present throughout parts of the OP
    src_g = core.std.Expr(src, ["", "", "x 32768 = x x 96 + ?"])
    src_g = lvf.rfs(src, src_g, [(None, 873)])

    scaled, descale_mask = flt.rescaler(src_g, height=854, shader_file=shader_file)

    # Denoising this is rough. Lots of fine detail that's easy to destroy.
    detail_mask = flt.detail_mask(scaled, pf_sigma=1.5, rxsigma=[50, 150, 200, 300], rad=2, brz=[2250, 3500])
    denoise_y = eoe.dn.BM3D(scaled, sigma=[0.3, 0])
    denoise_y_str = flt.to_yuvps(DPIR(flt.to_rgbs(scaled), strength=40, task='deblock', device_type='cpu'))
    denoise_y = lvf.rfs(denoise_y, denoise_y_str, [(1384, 1398)])

    denoise_uv = ccd(denoise_y, threshold=7, matrix='709')
    denoise_uv_rep = core.std.MaskedMerge(denoise_uv, denoise_y, detail_mask)
    stab = haf.GSMC(denoise_uv_rep, radius=1, thSAD=200, planes=[0])
    stab = lvf.rfs(stab, scaled, [(1399, 1400), (1408, 1416)])  # Undo denoising because it eats lines on these scenes
    decs = vdf.noise.decsiz(stab, sigmaS=8, min_in=200 << 8, max_in=232 << 8)

    # Fuck ufo lines
    eed = lvf.aa.nneedi3_clamp(decs, strength=1.6)
    sraa = lvf.sraa(decs, rfactor=1.5, aafun=flt.eedi3_singlerate_custom)
    clamp_aa = lvf.aa.clamp_aa(decs, eed, sraa, strength=1.6)

    # Certain frames have truly godawful aliasing. We attempt to fix those here
    tsraa = flt.transpose_sraa(decs, rfactor=1.5, aafun=flt.eedi3_singlerate_custom)
    tsraa_rep = core.rgvs.Repair(tsraa, clamp_aa, 13)
    aa_rfs = lvf.rfs(clamp_aa, tsraa_rep, strong_aa)

    # Fuck ufo lines
    ec = haf.EdgeCleaner(aa_rfs, strength=4)

    # This fixes up all the super red scenes fairly well
    crecon = lvf.recon.chroma_reconstruct(ec)

    deband_a = flt.masked_f3kdb(crecon, rad=18, thr=24, grain=[24, 16], mask_args={'brz': (1250, 2250)})
    deband_b = flt.masked_f3kdb(crecon, rad=24, thr=40, grain=[32, 24], mask_args={'brz': (1000, 1750)})
    deband_c = flt.placebo_debander(crecon, grain=2, iterations=2, threshold=8, radius=16)
    deband = lvf.rfs(deband_a, deband_b, [])
    deband = kgf.crossfade(deband[:2246+48], deband_c[2246:], 47)
    deband = lvf.rfs(deband, crecon, [(1399, 1400)])

    sqmask = lvf.mask.BoundingBox((699, 50), (526, 870)).get_mask(deband)
    sqmask = core.bilateral.Gaussian(sqmask, sigma=4)
    blur = core.bilateral.Gaussian(deband, sigma=25).bilateral.Gaussian(sigma=25)
    blur_mask = core.std.MaskedMerge(blur, deband, sqmask)
    blurred = kgf.crossfade(deband[:2412+48], blur_mask[2411:], 48)

    blurred_del = core.std.DeleteFrames(blurred, [2293])

    grain_a = adptvgrnMod(blurred_del, seed=42069, strength=0.15, static=True,
                          size=1.15, sharp=80, grain_chroma=False)
    grain_b = adptvgrnMod(blurred_del, seed=42069, strength=0.25, static=True,
                          size=1.15, sharp=100, grain_chroma=False)
    grain_c = adptvgrnMod(blurred_del, seed=42069, strength=0.2, static=False,
                          size=1.15, sharp=100, grain_chroma=False)
    grain = lvf.rfs(grain_a, grain_b, [(2390, None)])
    grain = lvf.rfs(grain, grain_c, [(885, 1149), (1324, 1345), (1489, 1506), (1603, 1810), (1981, 1996)])

    # Accidentally a frame during one of the previous processes. Easy to fix, though.
    oopsie = core.std.DeleteFrames(grain, [grain.num_frames-1])
    out = enc.dither_down(oopsie)

    return out


if __name__ == '__main__':
    enc.Encoder(JP_BD, filterchain()).run(clean_up=True, BDMV=True)  # type: ignore
elif __name__ == '__vapoursynth__':
    FILTERED = filterchain()
    if not isinstance(FILTERED, vs.VideoNode):
        raise ImportError(f"Input clip has multiple output nodes ({len(FILTERED)})! Please output a single clip")
    else:
        enc.dither_down(FILTERED).set_output(0)
else:
    pre_filter().std.SetFrameProp('node', intval=0).set_output(0)
    FILTERED = filterchain()
    if not isinstance(FILTERED, vs.VideoNode):
        for i, clip_filtered in enumerate(FILTERED, start=1):
            clip_filtered.std.SetFrameProp('node', intval=i).set_output(i)
    else:
        FILTERED.std.SetFrameProp('node', intval=1).set_output(1)
