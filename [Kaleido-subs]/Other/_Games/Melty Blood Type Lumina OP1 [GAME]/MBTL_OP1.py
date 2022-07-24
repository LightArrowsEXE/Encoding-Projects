from typing import Any, Dict, Tuple

import vapoursynth as vs
import vsencode as vse
from vardefunc import initialise_input

ini = vse.generate.init_project("x265")
shader = vse.get_shader("FSRCNNX_x2_56-16-4-1.glsl")
core = vse.util.get_vs_core(reserve_core=ini.reserve_core)


# Sources.
SRC = vse.FileInfo(f"{ini.bdmv_dir}/4mx21x.mkv")  # noqa


# OP/ED filtering.
opstart = 0


# Scenefiltering and zoning.
zones: Dict[Tuple[int, int], Dict[str, Any]] = {  # Zones for the encoder.
}


@initialise_input(bits=32)
def filterchain(src: vs.VideoNode = SRC.clip_cut) -> vs.VideoNode | Tuple[vs.VideoNode, ...]:
    """Main filterchain"""
    import havsfunc as haf  # type:ignore
    import lvsfunc as lvf
    import vardefunc as vdf
    import vsdehalo as vsdh
    import vskernels as kernels
    from debandshit import dumb3kdb, placebo_deband
    from stgfunc import Grainer, adaptive_grain
    from vsdehalo import contrasharpening_dehalo  # type:ignore
    from vsrgtools import contrasharpening, sbr
    from vsutil import depth, get_w

    assert src.format

    # Preparing clips
    src = src.resize.Point(chromaloc_in=0, chromaloc=1)

    # Upscaling
    fscrnnx = vdf.scale.fsrcnnx_upscale(
        src, get_w(1080), 1080, shader, downscaler=lvf.scale.ssim_downsample,
        overshoot=1.5, undershoot=1.5, profile='slow', strength=40
    )

    nnedi3 = kernels.BicubicDidee().scale(vdf.nnedi3_upscale(src), fscrnnx.width, fscrnnx.height)
    upscale = vdf.misc.merge_chroma(fscrnnx, nnedi3)
    upscale = vdf.to_444(upscale, upscale.width, upscale.height, True)

    # Deblocking
    dpir = lvf.dpir(upscale, strength=25, tiles=8, overlap=16, i444=True)
    upscale, dpir = [depth(clip, 16) for clip in [upscale, dpir]]

    csharp = contrasharpening(dpir, upscale)
    csharp = contrasharpening_dehalo(csharp, upscale)

    # Dehaloing. Converting to OPP for additional accuracy
    dehalo_opp = kernels.Catrom().resample(csharp, vs.RGB24).bm3d.RGB2OPP(0)

    dering = haf.HQDeringmod(dehalo_opp, mthr=24, minp=3, nrmode=2, sharp=0, darkthr=0, planes=[0])
    fdehalo = vsdh.fine_dehalo(dehalo_opp, rx=2, ry=2, thma=204, darkstr=0.15, planes=[0])
    dehalo = core.akarin.Expr([dehalo_opp, dering, fdehalo], ["x y - abs x z - abs < y z ?", ""])
    dehalo = vsdh.fine_dehalo(dehalo_opp, dehalo, planes=[0])

    dehalo_dark = vsdh.dehalo_alpha(dehalo, rx=4, ry=4, darkstr=0.25, brightstr=0, planes=[0])
    dehalo_dark = core.akarin.Expr([dehalo, dehalo_dark], "x y max")
    dehalo_uv = vsdh.dehalo_alpha(dehalo_dark, rx=3, ry=3, darkstr=0.25, brightstr=0.55, planes=[2])
    dehalo_csharp = contrasharpening(dehalo_uv, dehalo)

    dehalo_yuv = kernels.Catrom().resample(dehalo_csharp.bm3d.OPP2RGB(0), vs.YUV420P16, 1)
    darken = haf.FastLineDarkenMOD(dehalo_yuv, 32, protection=12)

    # Debanding
    detail_mask = lvf.mask.detail_mask_neo(darken, detail_brz=0.005, lines_brz=0.012)
    detail_mask = sbr(detail_mask, 3)

    deband = core.average.Mean([
        dumb3kdb(darken, radius=18, threshold=[24, 16], grain=[16, 12]),
        dumb3kdb(darken, radius=21, threshold=[32, 24], grain=[24, 16]),
        placebo_deband(darken, iterations=2, threshold=5, radius=20, grain=4),
    ]).std.MaskedMerge(darken, detail_mask)
    deband = contrasharpening(deband, darken)

    # Cleaning super bright areas
    decs = vdf.decsiz(deband, min_in=200 << 8, max_in=240 << 8)

    # Graining
    grain = adaptive_grain(
        decs, [2.25, 0.35], luma_scaling=8, static=False, temporal_average=100,
        grainer=Grainer.AddNoise, size=2.0, type=3, every=2, seed=69420
    )

    return grain


FILTERED = filterchain()


if __name__ == "__main__":
    runner = vse.EncodeRunner(SRC, FILTERED)
    runner.video(zones=zones)
    runner.audio("flac", external_audio_file="./stack black.flac")
    runner.mux("LightArrowsEXE@Kaleido")
    runner.run()
elif __name__ == "__vapoursynth__":
    if not isinstance(FILTERED, vs.VideoNode):
                raise vs.Error(f"Input clip has multiple output nodes ({len(FILTERED)})! "
                               "Please output a single clip")
    else:
        vse.video.finalize_clip(FILTERED).set_output(0)
else:
    SRC.clip_cut.set_output(0)

    if not isinstance(FILTERED, vs.VideoNode):
        for i, clip_filtered in enumerate(FILTERED, start=1):
            clip_filtered.set_output(i)
    else:
        FILTERED.set_output(1)

    for i, audio_node in enumerate(SRC.audios_cut, start=10):
        audio_node.set_output(i)
