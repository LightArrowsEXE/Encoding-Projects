import os
from pathlib import Path
from typing import Any, Dict, Tuple, Union

import vapoursynth as vs
from lvsfunc.misc import source
from vardautomation import FileInfo, PresetBD, PresetFLAC, VPath

from project_module import encoder as enc
from project_module import flt

core = vs.core


shader_file = 'assets/FSRCNNX_x2_16-0-4-1.glsl'
if not Path(shader_file).exists():
    hookpath = r"mpv/shaders/FSRCNNX_x2_16-0-4-1.glsl"
    shader_file = os.path.join(str(os.getenv("APPDATA")), hookpath)


# Sources
JP_BD = FileInfo(r"E:/src/Idol Time PriPara/IDOL_TIME_PRIPARA_BDBOX4_D2/BDMV/STREAM/00014.m2ts", (24, -24),
                 idx=lambda x: source(x, force_lsmas=True, cachedir=''), preset=[PresetBD, PresetFLAC])
JP_BD.name_file_final = VPath(fr"premux/{JP_BD.name} (Premux).mkv")
JP_BD.a_src_cut = JP_BD.name
JP_BD.do_qpfile = True


zones: Dict[Tuple[int, int], Dict[str, Any]] = {  # Zones for x265
}


def filterchain() -> Union[vs.VideoNode, Tuple[vs.VideoNode, ...]]:
    """Main VapourSynth filterchain"""
    import havsfunc as haf
    import lvsfunc as lvf
    import vardefunc as vdf
    from ccd import ccd
    from muvsfunc import SSIM_downsample
    from vsutil import depth, get_y

    src = JP_BD.clip_cut
    src = depth(src, 32)

    src_y = get_y(src)
    l_mask = vdf.mask.FDOG().get_mask(src_y, lthr=0.065, hthr=0.065).std.Maximum().std.Minimum()
    l_mask = l_mask.std.Median().std.Convolution([1] * 9)

    # Rescaling
    descale = flt.auto_descale(src_y)

    supersample = vdf.scale.nnedi3cl_double(descale, use_znedi=True, pscrn=1)
    downscaled = SSIM_downsample(supersample, src.width, src.height, smooth=((3 ** 2 - 1) / 12) ** 0.5,
                                 sigmoid=True, filter_param_a=0, filter_param_b=0)

    scaled_mask = core.std.MaskedMerge(src_y, downscaled, l_mask)
    scaled = depth(vdf.misc.merge_chroma(scaled_mask, src), 16)

    # Denoising
    l_mask_16 = depth(l_mask, 16).std.Minimum()
    dft = core.dfttest.DFTTest(scaled, sigma=1.25, tbsize=3, tosize=1)
    dft_masked = core.std.MaskedMerge(dft, scaled, l_mask_16)

    ccd_uv = ccd(dft, threshold=4, matrix='709')
    ccd_uv = core.std.MaskedMerge(ccd_uv, dft_masked, l_mask_16, planes=[1, 2])

    decs = vdf.noise.decsiz(ccd_uv, sigmaS=4, min_in=212 << 8, max_in=240 << 8)

    # AA and slight lineart enhancement
    baa = lvf.aa.based_aa(decs, shader_file)
    sraa = lvf.sraa(decs, rfactor=1.5, downscaler=lvf.kernels.Bicubic(b=-1/2, c=1/4).scale)
    clmp = lvf.aa.clamp_aa(decs, baa, sraa, strength=1.5)

    sraa_strong = flt.transpose_sraa(decs, rfactor=1.2, downscaler=lvf.kernels.Bicubic(b=-1/2, c=1/4).scale)
    clmp = lvf.rfs(clmp, sraa_strong, [])

    darken = haf.FastLineDarkenMOD(clmp, strength=36)

    # Debanding and graining
    deband = core.average.Mean([
        flt.masked_f3kdb(darken, rad=18, thr=[28, 24]),
        flt.masked_placebo(darken, rad=15, thr=4)
    ])

    grain = vdf.noise.Graigasm(
        thrs=[x << 8 for x in (32, 80, 128, 176)],
        strengths=[(0.15, 0.0), (0.10, 0.0), (0.10, 0.0), (0.0, 0.0)],
        sizes=(1.15, 1.10, 1.05, 1),
        sharps=(60, 50, 50, 50),
        grainers=[
            vdf.noise.AddGrain(seed=69420, constant=True),
            vdf.noise.AddGrain(seed=69420, constant=True),
            vdf.noise.AddGrain(seed=69420, constant=True)
        ]).graining(deband)

    return grain


if __name__ == '__main__':
    FILTERED = filterchain()
    enc.Encoder(JP_BD, FILTERED).run(clean_up=True, zones=zones)  # type: ignore
elif __name__ == '__vapoursynth__':
    FILTERED = filterchain()
    if not isinstance(FILTERED, vs.VideoNode):
        raise ImportError(
            f"Input clip has multiple output nodes ({len(FILTERED)})! Please output just 1 clip"
        )
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
