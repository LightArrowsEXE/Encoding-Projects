from __future__ import annotations

import ntpath
from glob import glob
from typing import Any, Dict, List, Tuple

import vapoursynth as vs
import vsencode as vse
from lvsfunc.types import VSDPIR_STRENGTH_TYPE, Range
from vardefunc import initialise_input

from project_module.filter import process_fileinfo

ini = vse.generate.init_project(venc_mode='x265')

core = vse.util.get_vs_core(reserve_core=ini.reserve_core)

shader = vse.get_shader("FSRCNNX_x2_56-16-4-1.glsl")

VSDPIR_STRENGTH_TYPE = List[Tuple[Range | List[Range], SupportsFloat | Any | None]]


# Sources
SRC = vse.FileInfo(f"{glob(f'{ini.bdmv_dir}/*{ntpath.basename(__file__)[-5:-3]} (*[*.mkv')[0]}")
SRC = process_fileinfo(SRC)

# Freezeframing
ff_first: List[int] = [
]

ff_last: List[int] = [
]

ff_repl: List[int] = [
]


# Scenefiltering
no_scaled: List[Range] = [  # Ranges that should not be rescaled
]

deblock_zones: List[Tuple[Range | List[Range], VSDPIR_STRENGTH_TYPE]] = [  # Ranges that require strong deblocking
]


zones: Dict[Tuple[int, int], Dict[str, Any]] = {  # Zones for the encoder
}

for k, v in zones:
    deblock_zones.append(((k, v), 50))  # type:ignore

deblock_ranges: List[Range] = [x[0] for x in deblock_zones]  # type:ignore

deblock_ranges + [
]


@initialise_input()
def filterchain(src: vs.VideoNode = SRC.clip_cut) -> vs.VideoNode | Tuple[vs.VideoNode, ...]:
    """Main filterchain."""
    import adptvgrnMod as adp
    import debandshit as dbs
    import havsfunc as haf
    import lvsfunc as lvf
    import vardefunc as vdf
    import vsdenoise as vsd
    import vsmask as vsm
    from finedehalo import fine_dehalo
    from vskernels import kernels
    from vsutil import depth, get_w, get_y, iterate

    from project_module import flt

    assert src.format

    cdmgl = depth(flt.chroma_demangle(src), 32)

    # Rescaling
    with vdf.YUVPlanes(cdmgl) as planes:
        src_y = planes.Y

        l_mask = vsm.edge.FDoG().edgemask(src_y, lthr=0.125, hthr=0.025).rgsf.RemoveGrain(4).rgsf.RemoveGrain(4)
        l_mask = l_mask.std.Minimum().std.Deflate().std.Median().std.Convolution([1] * 9).std.Limiter()
        sq_mask = lvf.mask.BoundingBox((4, 4), (src.width-4, src.height-4)).get_mask(src_y).std.Invert().std.Limiter()

        descale = kernels.Catrom().descale(src_y, get_w(874), 874)
        upscale = kernels.Catrom().scale(descale, src.width, src.height)

        credit_mask = lvf.scale.descale_detail_mask(src_y, upscale, threshold=0.075)
        credit_mask = iterate(credit_mask, core.std.Inflate, 2)
        credit_mask = iterate(credit_mask, core.std.Maximum, 2)
        credit_mask = core.akarin.Expr([credit_mask, sq_mask], "x y -").std.Limiter()

        rescale = vdf.scale.fsrcnnx_upscale(descale, src.width, src.height, shader,
                                            downscaler=lvf.scale.ssim_downsample,
                                            overshoot=1.1, undershoot=1.5,
                                            profile='slow', strength=25)
        rescale_min = core.akarin.Expr([rescale, src_y], "x y min")
        merge_lineart = core.std.MaskedMerge(src_y, depth(rescale_min, 32), l_mask)
        merge_credits = core.std.MaskedMerge(merge_lineart, src_y, credit_mask)
        planes.Y = lvf.rfs(merge_credits, src_y, no_scaled)

    scaled = depth(planes.clip, 16)

    # Denoising
    ref = haf.SMDegrain(get_y(scaled), tr=3, thSAD=150, Str=2.5)
    bm3d = depth(vsd.BM3DCudaRTC(scaled, [0.55, 0], radius=3, ref=ref).clip, 32)
    wnnm = core.wnnm.WNNM(bm3d, [0, 3.0], radius=0, group_size=7, bm_range=9)
    decs = vdf.noise.decsiz(depth(wnnm, 16), min_in=200 << 8, max_in=240 << 8)

    # Sometimes a scene is so heavily blocked, we need to deblock it.
    debl = lvf.vsdpir(decs, strength=0, tiles=8, overlap=8, zones=deblock_zones)
    debl = lvf.rfs(decs, debl, deblock_ranges)

    dering = haf.HQDeringmod(debl, mthr=24, nrmode=2, sharp=0, darkthr=0)
    fdehalo = haf.FineDehalo(debl, rx=2, ry=2, thma=204, darkstr=0)
    dehalo = core.std.Expr([debl, dering, fdehalo], "x y - abs x z - abs < y z ?")
    dehalo = fine_dehalo(debl, dehalo)

    ec = haf.EdgeCleaner(dehalo, strength=15)
    ec = core.akarin.Expr([dehalo, ec], "y 32768 < x y min x y max ?")

    if ff_first:
        ec = ec.std.FreezeFrames(ff_first, ff_last, ff_repl)

    detail_mask = lvf.mask.detail_mask(ec, rad=4, brz_a=0.015, brz_b=0.05)
    deband = core.std.MaskedMerge(core.average.Mean([
        dbs.dumb3kdb(ec, radius=18, threshold=[20, 16], grain=[12, 6]),
        dbs.dumb3kdb(ec, radius=21, threshold=[32, 24], grain=[24, 12]),
        dbs.placebo_deband(ec, threshold=3, iterations=2, grain=[4, 0])
    ]), ec, detail_mask)

    grain = adp.adptvgrnMod(deband, luma_scaling=10, static=False, temporal_average=50,
                            grainer=lambda x: core.noise.Add(x, xsize=3.5, ysize=3.5, var=2.0, uvar=0.35,
                                                             type=3, every=2, seed=69420))

    return grain


FILTERED = filterchain()


if __name__ == '__main__':
    assert isinstance(FILTERED, vs.VideoNode)
    vse.EncodeRunner(SRC, FILTERED) \
        .video('x265', '.settings/x265_settings', zones=zones) \
        .audio('passthrough') \
        .mux('LightArrowsEXE@GoodJobMedia').run()
elif __name__ == '__vapoursynth__':
    if not isinstance(FILTERED, vs.VideoNode):
        raise vs.Error(f"Input clip has multiple output nodes ({len(FILTERED)})! Please output a single clip")
    else:
        vse.video.finalize_clip(FILTERED).set_output(0)
else:
    SRC.clip_cut.set_output(0)

    if not isinstance(FILTERED, vs.VideoNode):
        for i, clip_filtered in enumerate(FILTERED, start=1):
            clip_filtered.set_output(i)
            if i == 10:
                print("Warning! More than 10 output nodes set! Stopping more from being output...")
                break
    else:
        FILTERED.set_output(1)

    for i, audio_node in enumerate(SRC.audios_cut, start=10):
        audio_node.set_output(i)
