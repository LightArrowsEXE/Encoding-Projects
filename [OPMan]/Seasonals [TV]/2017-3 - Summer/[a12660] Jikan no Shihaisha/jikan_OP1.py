from typing import Tuple, Union

import vapoursynth as vs
from lvsfunc.misc import source
from vardautomation import FileInfo, PresetAAC, PresetWEB, VPath

from project_module import enc, flt

core = vs.core
core.num_threads = 4

# Sources
JP_CR = FileInfo(r'websrc/CHRONOS RULER E13 [1080p][AAC][JapDub][GerEngSub][Web-DL].mkv', (1224, 3381),
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
    from vsutil import depth, get_w, get_y
    from xvs import WarpFixChromaBlend

    src_path = [
        r"websrc/CHRONOS RULER E05 [1080p][AAC][JapDub][GerEngSub][Web-DL].mkv",
        r"websrc/CHRONOS RULER E06 [1080p][AAC][JapDub][GerEngSub][Web-DL].mkv",
        r"websrc/CHRONOS RULER E07 [1080p][AAC][JapDub][GerEngSub][Web-DL].mkv",
        r"websrc/CHRONOS RULER E08 [1080p][AAC][JapDub][GerEngSub][Web-DL].mkv",
        r"websrc/CHRONOS RULER E09 [1080p][AAC][JapDub][GerEngSub][Web-DL].mkv",
        r"websrc/CHRONOS RULER E10 [1080p][AAC][JapDub][GerEngSub][Web-DL].mkv",
        r"websrc/CHRONOS RULER E11 [1080p][AAC][JapDub][GerEngSub][Web-DL].mkv",
        r"websrc/CHRONOS RULER E12 [1080p][AAC][JapDub][GerEngSub][Web-DL].mkv",
        r"websrc/CHRONOS RULER E13 [1080p][AAC][JapDub][GerEngSub][Web-DL].mkv"
    ]

    base = JP_CR.clip_cut
    src = [lvf.src(c, force_lsmas=True, cachedir='') for c in src_path]
    src_c = lvf.src(src_path[-3], force_lsmas=True, cachedir='')

    # Trimming clips to get just the OP
    src[0] = src[0][2182] * 11 + src[0][2182:2182+base.num_frames-11]
    src[1] = src[1][936:936+base.num_frames]
    src[2] = src[2][1104:1104+base.num_frames]
    src[3] = src[3][6378:6378+base.num_frames]
    src[4] = src[4][5179:5179+base.num_frames]
    src[5] = src[5][1200:1200+base.num_frames]
    src[6] = src[6][1822:1822+base.num_frames]
    src[7] = src[7][1558:1558+base.num_frames]
    src[8] = src[8][1224:1224+base.num_frames]

    mean = core.average.Mean(src)  # type:ignore[attr-defined]
    mean = mean[:-1] + src_c[1822:3980][-2:]
    mean = depth(mean, 32)

    mean_y = get_y(mean)
    descale = lvf.kernels.Lanczos(taps=5).descale(mean_y, get_w(945), 945)
    rescale = vdf.scale.nnedi3cl_double(descale, pscrn=1)
    rescale = muf.SSIM_downsample(rescale, mean_y.width, mean_y.height)
    scaled = vdf.misc.merge_chroma(rescale, mean)
    scaled = depth(scaled, 16)

    decs = vdf.noise.decsiz(scaled, sigmaS=8, min_in=208 << 8, max_in=232 << 8)

    deband_reg = flt.masked_f3kdb(decs, thr=24, grain=[24, 12])

    detail_mask = flt.detail_mask(decs, brz=(1200, 3000))
    den_ref = core.knlm.KNLMeansCL(decs, d=1, a=3, s=4, h=0.5, channels='Y')
    deband_str = flt.placebo_debander(den_ref, placebo_args={'threshold': 4})
    deband_str = core.std.MaskedMerge(deband_str, deband_reg, detail_mask)

    deband = lvf.rfs(deband_reg, deband_str, [(1162, 1193), (1210, 1216)])

    grain: vs.VideoNode = adptvgrnMod(deband, seed=42069, strength=0.3, luma_scaling=8,
                                      size=1.35, sharp=100, grain_chroma=False)

    return grain


if __name__ == '__main__':
    FILTERED = filterchain()
    enc.Encoder(JP_CR, FILTERED).run(clean_up=True)  # type: ignore[arg-type]
    #enc.Patcher(JP_CR, FILTERED).patch(ranges=[(1162, 1216), (2059, 2157)])  # type: ignore[arg-type]
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
