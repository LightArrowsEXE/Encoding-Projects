from typing import Optional, Sequence, Tuple, Union

import vapoursynth as vs
from lvsfunc.misc import source
from vardautomation import (JAPANESE, FileInfo, MplsReader, PresetAAC,
                            PresetBD, VPath)

from project_module import enc, flt

core = vs.core
core.num_threads = 4

EP_NUM = __file__[-5:-3]


# Sources
JP_BD = FileInfo(r'BDMV/[BDMV][210224][Majo no Tabitabi][Blu-Ray BOX下巻]/BDMV/STREAM/00006.m2ts',
                 (24, -24), idx=lambda x: source(x, force_lsmas=True, cachedir=''),
                 preset=[PresetBD, PresetAAC])
JP_BD_NCED = FileInfo(r'BDMV/[BDMV][アニメ][210127][MAJO_NO_TABITABI_1][Blu-Ray BOX 上]/BDMV/STREAM/00016.m2ts',
                     (24, -24), idx=lambda x: source(x, force_lsmas=True, cachedir=''))
JP_WEB = FileInfo(fr'WebSrc/Wandering Witch Elaina E{EP_NUM} [1080p][AAC][JapDub][GerSub][Web-DL].mkv',
                  (None, None), idx=lambda x: source(x, force_lsmas=True, cachedir=''))
JP_BD.name_file_final = VPath(f"premux/{JP_BD.name} (Premux).mkv")
JP_BD.a_src_cut = VPath(f"{JP_BD.name}_cut.aac")
JP_BD.do_qpfile = True


# Chapter creation
CHAPTERS = MplsReader(r"BDMV/[BDMV][210224][Majo no Tabitabi][Blu-Ray BOX下巻]", lang=JAPANESE) \
    .get_playlist()[1].mpls_chapters[int(EP_NUM)-13].to_chapters()
CHAP_NAMES: Sequence[Optional[str]] = ['Intro', 'OP', 'Part A', 'Part B', 'Outro']


# ED Variables
edstart = False
ed_offset = 2


def pre_corrections() -> Union[vs.VideoNode, Tuple[vs.VideoNode, ...]]:
    """
    There were a couple animation 'fixes' in the BDs that I'm reverting here.
    Alongside that, they also introduced a couple of errors occasionally which I also fix here.
    Comments with examples of what I'm changing/fixing included if big enough.
    """
    import lvsfunc as lvf

    src_BD = JP_BD.clip_cut
    src_WEB = JP_WEB.clip_cut

    # No fixes in this episode
    fixed = src_BD

    return fixed


def filterchain() -> Union[vs.VideoNode, Tuple[vs.VideoNode, ...]]:
    """Main filterchain"""
    import havsfunc as haf
    import lvsfunc as lvf
    import rekt
    import vardefunc as vdf
    from adptvgrnMod import adptvgrnMod
    from ccd import ccd
    from vsutil import depth, get_w, get_y

    src: vs.VideoNode = pre_corrections()  # type:ignore[assignment]
    src_NCED = JP_BD_NCED.clip_cut

    # Masking credits
    ed_mask = vdf.dcm(
        src, src[edstart:edstart+src_NCED.num_frames-ed_offset], src_NCED[:-ed_offset],
        start_frame=edstart, thr=25, prefilter=False) if edstart is not False \
        else get_y(core.std.BlankClip(src))
    credit_mask = depth(ed_mask, 16).std.Binarize()

    rkt = rekt.rektlvls(src, [0, 1079], [7, 7], [0, 1919], [7, 7], prot_val=None)
    rkt = depth(rkt, 16)

    denoise_uv = ccd(rkt, threshold=7, matrix='709')
    stab = haf.GSMC(denoise_uv, radius=1, thSAD=200, planes=[0])
    decs = vdf.noise.decsiz(stab, sigmaS=8, min_in=208 << 8, max_in=232 << 8)

    l_mask = vdf.mask.FDOG().get_mask(get_y(decs), lthr=0.065, hthr=0.065).std.Maximum().std.Minimum()
    l_mask = l_mask.std.Median().std.Convolution([1] * 9)

    aa_weak = lvf.aa.taa(decs, lvf.aa.nnedi3(opencl=True))
    aa_strong = lvf.aa.upscaled_sraa(decs, downscaler=lvf.kernels.Bicubic(b=-1/2, c=1/4).scale)
    aa_clamp = lvf.aa.clamp_aa(decs, aa_weak, aa_strong, strength=1.5)
    aa_masked = core.std.MaskedMerge(decs, aa_clamp, l_mask)

    dehalo = haf.FineDehalo(aa_masked, rx=1.6, ry=1.6, darkstr=0, brightstr=1.25)
    darken = flt.line_darkening(dehalo, 0.275).warp.AWarpSharp2(depth=2)

    merged_credits = core.std.MaskedMerge(darken, decs, credit_mask)

    deband = flt.masked_f3kdb(merged_credits, rad=18, thr=32, grain=[32, 12])
    grain: vs.VideoNode = adptvgrnMod(deband, seed=42069, strength=0.35, luma_scaling=8,
                                      size=1.05, sharp=80, grain_chroma=False)

    return grain


if __name__ == '__main__':
    FILTERED = filterchain()
    enc.Encoder(JP_BD, FILTERED, CHAPTERS, CHAP_NAMES).run(clean_up=True)  # type: ignore
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
    #FILTERED = pre_corrections()
    FILTERED = filterchain()
    if not isinstance(FILTERED, vs.VideoNode):
        for i, clip_filtered in enumerate(FILTERED, start=1):
            clip_filtered.std.SetFrameProp('node', intval=i).set_output(i)
    else:
        FILTERED.std.SetFrameProp('node', intval=1).set_output(1)
