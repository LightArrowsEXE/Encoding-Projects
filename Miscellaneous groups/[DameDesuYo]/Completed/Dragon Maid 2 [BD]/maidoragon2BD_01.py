import os
from functools import partial
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple, Union

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
    shader_file = os.path.join(str(os.getenv("APPDATA")), hookpath)

use_cuda: bool = __name__ == '__main__'


# Sources
JP_BD = FileInfo(r'BDMV/[BDMV][210915][PCXE-51001][小林さんちのメイドラゴンS][Vol.1]/MAIDRAGON_S_1/BDMV/STREAM/00000.m2ts',
                 (None, -35), idx=lambda x: source(x, force_lsmas=True, cachedir=''), preset=[PresetBD, PresetFLAC])
JP_OP = FileInfo(r'BDMV/[BDMV][211225][PCXE-51004][小林さんちのメイドラゴンS][Vol.4]/MAIDRAGON_S_4/BDMV/STREAM/00004.m2ts',
                 (None, -24), idx=lambda x: source(x, force_lsmas=True, cachedir=''))
JP_ED = FileInfo(r'BDMV/[BDMV][211225][PCXE-51004][小林さんちのメイドラゴンS][Vol.4]/MAIDRAGON_S_4/BDMV/STREAM/00005.m2ts',
                 (None, -24), idx=lambda x: source(x, force_lsmas=True, cachedir=''))
JP_BD.name_file_final = VPath(fr"premux/{JP_BD.name} (Premux).mkv")
JP_BD.a_src_cut = VPath(JP_BD.name)
JP_BD.do_qpfile = True


# OP/ED filtering
opstart = 1606
edstart = 31408
op_offset = 1
ed_offset = 3


# Scenefiltering
stronger_deblock_ranges: Iterable[Range] = [  # Heavy compression artefacting
    (7021, 7148), (18761, 18878), (20553, 20582)
]


zones: Dict[Tuple[int, int], Dict[str, Any]] = {  # Zones for x265
}


def filterchain() -> Union[vs.VideoNode, Tuple[vs.VideoNode, ...]]:
    """Main filterchain"""
    import EoEfunc as eoe
    import havsfunc as haf
    import lvsfunc as lvf
    import vardefunc as vdf
    from ccd import ccd
    from vsutil import depth, get_y, insert_clip

    src = JP_BD.clip_cut
    src_c = src
    src_ncop, src_nced = JP_OP.clip_cut, JP_ED.clip_cut
    b = core.std.BlankClip(src, length=1)

    # OP/ED stack comps to check if they line up
    if opstart is not False:
        op_scomp = lvf.scomp(src[opstart:opstart+src_ncop.num_frames-1]+b, src_ncop[:-op_offset]+b)  # noqa
    if edstart is not False:
        ed_scomp = lvf.scomp(src[edstart:edstart+src_nced.num_frames-1]+b, src_nced[:-ed_offset]+b)  # noqa

    # Splicing in NCs and diff'ing back the credits
    if opstart is not False:
        src = insert_clip(src, src_ncop[:-op_offset], opstart)
    if edstart is not False:
        src = insert_clip(src, src_nced[:-ed_offset], edstart)

    den_src, den_ncs = map(partial(core.dfttest.DFTTest, sigma=10), [src_c, src])
    den_src, den_ncs = depth(den_src, 32), depth(den_ncs, 32)
    diff = core.std.MakeDiff(den_src, den_ncs).dfttest.DFTTest(sigma=100.0)

    # For some reason there's noise from previous credits remaining? Removing that here
    diff_brz = vdf.misc.merge_chroma(depth(depth(diff.std.Binarize(0.025), 16).rgvs.RemoveGrain(3), 32), diff)
    diff = core.std.Expr([diff, diff_brz], "x y min")
    # return op_scomp, ed_scomp, diff

    src = depth(src, 16)
    src_y = get_y(src)

    # We wanna keep the denoising weak due to all the strong textures, but dark areas look so meh
    adap_mask = core.adg.Mask(src_y.std.PlaneStats(), 8).deblock.Deblock(24).dfttest.DFTTest(sigma=1.0)

    pre_dp = lvf.deblock.vsdpir(src, strength=5, mode='deblock', matrix=1, cuda=use_cuda)
    denoise_y_brgt = haf.SMDegrain(src, tr=3, thSAD=75, plane=0, chroma=False, prefilter=pre_dp, mfilter=pre_dp)
    denoise_y_dark = haf.SMDegrain(src, tr=3, thSAD=50, plane=0, chroma=False, prefilter=pre_dp, mfilter=pre_dp)
    denoise_y = core.std.MaskedMerge(denoise_y_brgt, denoise_y_dark, adap_mask)

    denoise = ccd(denoise_y, threshold=3, matrix='709')

    if stronger_deblock_ranges:  # But sometimes...
        # Just gonna have to pray the VRAM usage doesn't spike too hard and kills the encode lol
        deblock_str = lvf.deblock.vsdpir(denoise, strength=45, cuda=use_cuda, matrix=1)
        denoise = lvf.rfs(denoise, deblock_str, stronger_deblock_ranges)

    csharp = eoe.misc.ContraSharpening(denoise, src, 2, planes=[0])

    decs = vdf.noise.decsiz(csharp, sigmaS=8, min_in=208 << 8, max_in=232 << 8,
                            protect_mask=core.std.Prewitt(get_y(src), scale=0.5).std.Maximum())

    baa = lvf.aa.based_aa(decs, str(shader_file))
    sraa = lvf.sraa(decs, rfactor=1.7)
    clmp = lvf.aa.clamp_aa(decs, baa, sraa, strength=1.2)
    clmp = core.rgvs.Repair(clmp, decs, 13)

    deband = core.average.Mean([
        flt.masked_placebo(clmp, rad=3.5, thr=1.5, itr=2, grain=4),
        flt.masked_placebo(clmp, rad=5, thr=2.5, itr=2, grain=4),
        flt.zzdeband(clmp, denoised=True)
    ])

    grain = vdf.noise.Graigasm(
        thrs=[x << 8 for x in (32, 80, 128, 176)],
        strengths=[(0.20, 0.0), (0.15, 0.0), (0.10, 0.0), (0.0, 0.0)],
        sizes=(1.15, 1.10, 1.05, 1),
        sharps=(80, 70, 60, 50),
        grainers=[
            vdf.noise.AddGrain(seed=69420, constant=True),
            vdf.noise.AddGrain(seed=69420, constant=False),
            vdf.noise.AddGrain(seed=69420, constant=False)
        ]).graining(deband)

    merge_creds = core.std.MergeDiff(depth(grain, 32), diff)

    if opstart is not False:
        sqmask = lvf.mask.BoundingBox((6, 6), (src.width-12, src.height-12)).get_mask(merge_creds).std.Invert()
        ncop_ef = flt.edgefix_ncop(src, r'assets/NCOP1/maidoragon2BD_NCOP1_edgefix.ass', opstart)
        merge_creds = core.std.MaskedMerge(merge_creds, depth(ncop_ef, 32), sqmask)

    return merge_creds


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
