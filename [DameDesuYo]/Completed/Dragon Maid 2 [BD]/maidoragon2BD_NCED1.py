from typing import Any, Dict, List, Tuple, Union

import vapoursynth as vs  # type:ignore
import vsencode as vse
from lvsfunc.types import Range

ini = vse.generate.init_project('x265')

core = vse.util.get_vs_core(reserve_core=ini.reserve_core)

shader = vse.get_shader()


# Sources
JP_BD = vse.FileInfo(r'BDMV/[BDMV][211225][PCXE-51004][小林さんちのメイドラゴンS][Vol.4]/MAIDRAGON_S_4/BDMV/STREAM/00005.m2ts', (None, -24))  # noqa


# OP/ED filtering
opstart = False
edstart = 0
op_offset = 1
ed_offset = 1


# Scenefiltering
stronger_deblock_ranges: List[Range] = [  # Heavy compression artefacting
]


zones: Dict[Tuple[int, int], Dict[str, Any]] = {  # Zones for x265
}


def filterchain() -> Union[vs.VideoNode, Tuple[vs.VideoNode, ...]]:
    """Main filterchain"""
    import EoEfunc as eoe
    import havsfunc as haf
    import lvsfunc as lvf
    import vardefunc as vdf
    import jvsfunc as jvf
    from vsutil import depth, get_y

    from project_module import flt

    src = JP_BD.clip_cut

    src = depth(src, 16)
    src_y = get_y(src)

    # We wanna keep the denoising weak due to all the strong textures, but dark areas look so meh
    adap_mask = core.adg.Mask(src_y.std.PlaneStats(), 8).deblock.Deblock(24).dfttest.DFTTest(sigma=1.0)

    pre_dp = lvf.deblock.dpir(src, strength=5, mode='deblock', matrix=1)
    denoise_y_brgt = haf.SMDegrain(src, tr=3, thSAD=75, plane=0, chroma=False, prefilter=pre_dp, mfilter=pre_dp)
    denoise_y_dark = haf.SMDegrain(src, tr=3, thSAD=50, plane=0, chroma=False, prefilter=pre_dp, mfilter=pre_dp)
    denoise_y = core.std.MaskedMerge(denoise_y_brgt, denoise_y_dark, adap_mask)

    denoise = jvf.ccd(denoise_y, threshold=3, mode=3)

    if stronger_deblock_ranges:  # But sometimes...
        # Just gonna have to pray the VRAM usage doesn't spike too hard and kills the encode lol
        deblock_str = lvf.deblock.dpir(denoise, strength=45, matrix=1)
        denoise = lvf.rfs(denoise, deblock_str, stronger_deblock_ranges)

    csharp = eoe.misc.ContraSharpening(denoise, src, 2, planes=[0])

    decs = vdf.noise.decsiz(csharp, sigmaS=8, min_in=208 << 8, max_in=232 << 8,
                            protect_mask=core.std.Prewitt(get_y(src), scale=0.5).std.Maximum())

    baa = lvf.aa.based_aa(decs, shader)
    sraa = lvf.sraa(decs, rfactor=1.7)
    clmp = lvf.aa.clamp_aa(decs, baa, sraa, strength=1.2)
    clmp = core.rgvs.Repair(clmp, decs, 13)

    deband = core.average.Mean([
        flt.masked_placebo(clmp, rad=3, thr=1, itr=2, grain=4),
        flt.masked_placebo(clmp, rad=5, thr=2, itr=2, grain=4),
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

    if opstart is not False:
        sqmask = lvf.mask.BoundingBox((6, 6), (src.width-12, src.height-12)).get_mask(grain).std.Invert()
        ncop_ef = flt.edgefix_ncop(src, r'assets/NCOP1/maidoragon2BD_NCOP1_edgefix.ass', opstart)
        grain = core.std.MaskedMerge(grain, depth(ncop_ef, 16), sqmask)

    return grain


FILTERED = filterchain()


if __name__ == '__main__':
    runner = vse.EncodeRunner(JP_BD, FILTERED)
    runner.video(zones=zones)
    runner.audio('flac')
    runner.mux('LightArrowsEXE@DameDesuYo')
    runner.run()
elif __name__ == '__vapoursynth__':
    if not isinstance(FILTERED, vs.VideoNode):
        raise vs.Error(f"Input clip has multiple output nodes ({len(FILTERED)})! "
                       "Please output a single clip")
    else:
        vse.video.finalize_clip(FILTERED).set_output(0)
else:
    JP_BD.clip_cut.set_output(0)

    if not isinstance(FILTERED, vs.VideoNode):
        for i, clip_filtered in enumerate(FILTERED, start=1):
            clip_filtered.set_output(i)
    else:
        FILTERED.set_output(1)

    for i, audio_node in enumerate(JP_BD.audios_cut, start=10):
        audio_node.set_output(i)
