from typing import Tuple, Union

import vapoursynth as vs
from lvsfunc.misc import source
from vardautomation import FileInfo, PresetAAC, PresetBD, VPath

from project_module import enc, flt

core = vs.core
core.num_threads = 4


# Sources
JP_BD = FileInfo(r'BDMV/[BDMV][アニメ][210127][MAJO_NO_TABITABI_1][Blu-Ray BOX 上]/BDMV/STREAM/00016.m2ts', (24, -24),
                 idx=lambda x: source(x, force_lsmas=True, cachedir=''),
                 preset=[PresetBD, PresetAAC])
JP_BD.name_file_final = VPath(f"premux/{JP_BD.name} (Premux).mkv")
JP_BD.a_src_cut = VPath(f"{JP_BD.name}_cut.aac")
JP_BD.do_qpfile = True


def filterchain() -> Union[vs.VideoNode, Tuple[vs.VideoNode, ...]]:
    """Main filterchain"""
    import havsfunc as haf
    import lvsfunc as lvf
    import rekt
    import vardefunc as vdf
    from adptvgrnMod import adptvgrnMod
    from ccd import ccd
    from vsutil import depth, get_y

    src = JP_BD.clip_cut

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

    deband = flt.masked_f3kdb(darken, rad=18, thr=32, grain=[32, 12])
    grain: vs.VideoNode = adptvgrnMod(deband, seed=42069, strength=0.35, luma_scaling=8,
                                      size=1.05, sharp=80, grain_chroma=False)

    return grain


if __name__ == '__main__':
    FILTERED = filterchain()
    enc.Encoder(JP_BD, FILTERED).run(clean_up=True)  # type: ignore
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
