from typing import Tuple, Union

import vapoursynth as vs
from lvsfunc.misc import source
from vardautomation import FileInfo, PresetBD, PresetFLAC, VPath

from project_module import encoder as enc
from project_module import flt

core = vs.core

# Sources
JP_BD = FileInfo(r'BDMV/DISC7/BDMV/STREAM/00009.m2ts', (24, -24),
                 idx=lambda x: source(x, cachedir=''), preset=[PresetBD, PresetFLAC])
JP_BD.name_file_final = VPath(fr"premux/{JP_BD.name} (Premux).mkv")
JP_BD.a_src_cut = VPath(JP_BD.name)
JP_BD.do_qpfile = True


def filterchain() -> Union[vs.VideoNode, Tuple[vs.VideoNode, ...]]:
    """Main filterchain"""
    import havsfunc as haf
    import lvsfunc as lvf
    import vardefunc as vdf
    from adptvgrnMod import adptvgrnMod
    from ccd import ccd
    from vsutil import depth

    src = JP_BD.clip_cut
    src = depth(src, 16)

    scaled, descale_mask = flt.rescaler(src, height=855)

    denoise_y = core.knlm.KNLMeansCL(scaled, d=2, a=3, h=0.15)
    denoise_uv = ccd(denoise_y, threshold=7, matrix='709')
    denoise_uv_str = ccd(denoise_y, threshold=15, matrix='709')
    denoise_uv = lvf.rfs(denoise_uv, denoise_uv_str, [(1999, 2041)])

    stab = haf.GSMC(denoise_uv, radius=1, thSAD=200, planes=[0])
    decs = vdf.noise.decsiz(stab, sigmaS=8, min_in=200 << 8, max_in=232 << 8)

    aa_weak = lvf.aa.nneedi3_clamp(decs, strength=4)
    aa_strong = lvf.sraa(decs, rfactor=1.6)
    aa_clamp = lvf.aa.clamp_aa(decs, aa_weak, aa_strong, strength=2)

    halo_mask = lvf.mask.halo_mask(aa_clamp)
    darken = flt.line_darkening(aa_clamp, strength=0.35)
    dehalo = core.std.MaskedMerge(darken, lvf.dehalo.bidehalo(darken, sigmaS_final=1.2, sigmaR=11/255), halo_mask)

    # ufo w h y y y y y this is why I hate working on your shows
    halo_mask_str = lvf.mask.halo_mask(aa_clamp, rad=1, brz=0.9, thlima=0.55)
    dehalo_str = core.std.MaskedMerge(
        darken, lvf.dehalo.bidehalo(darken, sigmaS=4.0, sigmaS_final=3.6, sigmaR=22/255), halo_mask_str)
    dehalo = lvf.rfs(dehalo, dehalo_str, [(2042, 2077)])

    merged_credits = core.std.MaskedMerge(dehalo, src, descale_mask)

    deband = flt.masked_f3kdb(merged_credits, rad=21, thr=[28, 24], grain=[32, 16])
    grain: vs.VideoNode = adptvgrnMod(deband, seed=42069, strength=0.25, luma_scaling=10,
                                      size=1.35, sharp=80, grain_chroma=False)

    return grain


if __name__ == '__main__':
    FILTERED = filterchain()
    enc.Encoder(JP_BD, FILTERED).run(clean_up=True, make_comp=True)  # type: ignore
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
