from typing import Tuple, Union

import vapoursynth as vs
from lvsfunc.misc import source
from vardautomation import FileInfo, PresetAAC, PresetWEB, VPath

from project_module import enc, flt

core = vs.core
core.num_threads = 4

# Sources
JP_CR = FileInfo(r'websrc/CHRONOS RULER E12 [1080p][AAC][JapDub][GerEngSub][Web-DL].mkv', (31529, None),
                 idx=lambda x: source(x, force_lsmas=True, cachedir=''),
                 preset=[PresetWEB, PresetAAC])
JP_CR.name_file_final = VPath(f"premux/{JP_CR.name} (Premux).mkv")
JP_CR.a_src_cut = VPath(f"{JP_CR.name}_cut.aac")
JP_CR.do_qpfile = True


def filterchain() -> Union[vs.VideoNode, Tuple[vs.VideoNode, ...]]:
    """Main filterchain"""
    import lvsfunc as lvf
    import muvsfunc as muf
    import vardefunc as vdf
    from adptvgrnMod import adptvgrnMod
    from ccd import ccd
    from vsutil import depth, get_w, get_y, iterate

    # Can't mean this one out this time because of credit changes
    src = JP_CR.clip_cut
    src = depth(src, 32)

    src_y = get_y(src)
    descale = lvf.kernels.Lanczos(taps=5).descale(src_y, get_w(945), 945)
    rescale = vdf.scale.nnedi3cl_double(descale, pscrn=1)
    rescale = muf.SSIM_downsample(rescale, src_y.width, src_y.height)
    scaled = vdf.misc.merge_chroma(rescale, src)
    scaled = depth(scaled, 16)

    # Having a hard time reliably catching the EDs. Oh well.
    upscale = lvf.kernels.Lanczos(taps=5).scale(descale, src_y.width, src_y.height)
    credit_mask = depth(lvf.scale.descale_detail_mask(src_y, upscale, threshold=0.08), 16)
    credit_mask = iterate(credit_mask, core.std.Minimum, 5)
    credit_mask = iterate(credit_mask, core.std.Maximum, 9)
    credit_mask = core.morpho.Close(credit_mask, 9)

    credits_merged = core.std.MaskedMerge(scaled, depth(src, 16), credit_mask)

    denoise_y = core.knlm.KNLMeansCL(credits_merged, d=1, a=3, s=4, h=0.55, channels='Y')
    denoise_uv = ccd(denoise_y, threshold=6, matrix='709')
    decs = vdf.noise.decsiz(denoise_uv, sigmaS=8, min_in=208 << 8, max_in=232 << 8)

    darken = flt.line_darkening(decs, strength=0.175)

    deband = flt.masked_f3kdb(darken, thr=24, grain=[24, 12])
    grain: vs.VideoNode = adptvgrnMod(deband, seed=42069, strength=0.45, luma_scaling=10,
                                      size=1.25, sharp=100, static=True, grain_chroma=False)

    return grain


if __name__ == '__main__':
    FILTERED = filterchain()
    enc.Encoder(JP_CR, FILTERED).run(clean_up=True)  # type: ignore[arg-type]
    # enc.Patcher(JP_CR, FILTERED).patch(ranges=[(1162, 1216), (2059, 2157)])  # type: ignore[arg-type]
elif __name__ == '__vapoursynth__':
    FILTERED = filterchain()
    if not isinstance(FILTERED, vs.VideoNode):
        raise ImportError(
            f"Input clip has multiple output nodes ({len(FILTERED)})! Please output a single clip")
    else:
        enc.dither_down(FILTERED).set_output(0)
else:
    JP_CR.clip_cut.std.SetFrameProp('node', intval=0).set_output(0)
    FILTERED = filterchain()
    if not isinstance(FILTERED, vs.VideoNode):
        for i, clip_filtered in enumerate(FILTERED, start=1):
            clip_filtered.std.SetFrameProp('node', intval=i).set_output(i)
    else:
        FILTERED.std.SetFrameProp('node', intval=1).set_output(1)
