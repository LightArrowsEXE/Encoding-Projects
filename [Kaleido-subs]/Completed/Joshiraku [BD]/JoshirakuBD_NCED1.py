from typing import Tuple, Union

import vapoursynth as vs
from lvsfunc.misc import source
from vardautomation import FileInfo, PresetAAC, PresetBD, VPath

from project_module import encoder as enc, flt

core = vs.core
core.num_threads = 4


# Sources
JP_NCED = FileInfo(r'BDMV/120926_JOSHIRAKU_VOL1/BDMV/STREAM/00002.m2ts', (24, -24),
                   idx=lambda x: source(x, cachedir=''),
                   preset=[PresetBD, PresetAAC])
JP_NCED.name_file_final = VPath(fr"premux/{JP_NCED.name} (Premux).mkv")
JP_NCED.a_src_cut = VPath(f"{JP_NCED.name}_cut.aac")
JP_NCED.do_qpfile = True


def filterchain() -> Union[vs.VideoNode, Tuple[vs.VideoNode, ...]]:
    """Main filterchain"""
    import havsfunc as haf
    import lvsfunc as lvf
    import rekt
    import vardefunc as vdf
    from adptvgrnMod import adptvgrnMod
    from awsmfunc import bbmod
    from ccd import ccd
    from vsutil import depth, get_y
    from xvs import WarpFixChromaBlend

    src = JP_NCED.clip_cut

    # Edgefixing
    rkt = rekt.rektlvls(
        src,
        [0, 1079], [17, 16],
        [0, 1, 2, 3] + [1917, 1918, 1919], [16, 4, -2, 2] + [-2, 5, 14]
    )
    ef = bbmod(rkt, left=4, right=3, y=False)
    ef = depth(ef, 32)

    # Descaling + Rescaling
    src_y = get_y(ef)
    descaled = lvf.kernels.Bicubic().descale(src_y, 1280, 720)
    rescaled = vdf.scale.nnedi3_upscale(descaled)
    downscaled = lvf.kernels.Bicubic(-1/2, 1/4).scale(rescaled, 1920, 1080)

    l_mask = vdf.mask.FDOG().get_mask(src_y, lthr=0.065, hthr=0.065).std.Maximum().std.Minimum()
    l_mask = l_mask.std.Median().std.Convolution([1] * 9)

    rescaled_masked = core.std.MaskedMerge(src_y, downscaled, l_mask)
    scaled = depth(vdf.misc.merge_chroma(rescaled_masked, ef), 16)

    unwarp = flt.line_darkening(scaled, 0.145).warp.AWarpSharp2(depth=2)
    sharp = haf.LSFmod(unwarp, strength=65, Smode=3, Lmode=1, edgemode=1, edgemaskHQ=True)
    mask_sharp = core.std.MaskedMerge(scaled, sharp, depth(l_mask, 16))

    upscaled = lvf.kernels.Bicubic().scale(descaled, 1920, 1080)
    descale_mask = lvf.scale.descale_detail_mask(src_y, upscaled)
    details_merged = core.std.MaskedMerge(mask_sharp, depth(ef, 16), depth(descale_mask, 16))

    # Denoising
    denoise_y = core.knlm.KNLMeansCL(details_merged, d=1, a=3, s=4, h=0.15, channels='Y')
    denoise_uv = ccd(denoise_y, threshold=6, matrix='709')
    stab = haf.GSMC(denoise_uv, radius=2, adapt=1, planes=[0])
    decs = vdf.noise.decsiz(stab, sigmaS=8, min_in=208 << 8, max_in=232 << 8)

    # Fixing chroma
    cshift = haf.FixChromaBleedingMod(decs, cx=-.25, cy=0, thr=100, strength=1, blur=True)
    cwarp = WarpFixChromaBlend(cshift, thresh=88, blur=3, depth=6)

    # Regular debanding + graining
    detail_mask = flt.detail_mask(cwarp, brz=(1800, 3500))
    deband = vdf.deband.dumb3kdb(cwarp, threshold=32, grain=16)
    deband_masked = core.std.MaskedMerge(deband, cwarp, detail_mask)
    grain: vs.VideoNode = adptvgrnMod(deband_masked, 0.2, luma_scaling=10, size=1.35, static=True, grain_chroma=False)

    return grain


if __name__ == '__main__':
    FILTERED = filterchain()
    enc.Encoder(JP_NCED, FILTERED).run(clean_up=True)  # type: ignore
elif __name__ == '__vapoursynth__':
    FILTERED = filterchain()
    if not isinstance(FILTERED, vs.VideoNode):
        raise ImportError(
            f"Input clip has multiple output nodes ({len(FILTERED)})! Please output just 1 clip"
        )
    else:
        enc.dither_down(FILTERED).set_output(0)
else:
    JP_NCED.clip_cut.std.SetFrameProp('node', intval=0).set_output(0)
    FILTERED = filterchain()
    if not isinstance(FILTERED, vs.VideoNode):
        for i, clip_filtered in enumerate(FILTERED, start=1):
            clip_filtered.std.SetFrameProp('node', intval=i).set_output(i)
    else:
        FILTERED.std.SetFrameProp('node', intval=1).set_output(1)
