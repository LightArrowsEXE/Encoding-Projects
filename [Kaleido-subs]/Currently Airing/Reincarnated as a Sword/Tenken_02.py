from typing import Any, cast

import vapoursynth as vs  # type:ignore
import vsencode as vse

ini = vse.generate.init_project("x265")
core = vs.core
run = __name__ in ('__vapoursynth__', '__main__')

BGLOBAL = vse.FileInfo("src/Tensei shitara Ken Deshita - 02 (B-Global 2160p).mkv", (None, None))  # noqa
ABEMA = vse.FileInfo("src/[NanakoRaws] Tensei Shitara Ken Deshita - 02 (1080p).mp4", (None, None))  # noqa


# Scenefiltering

# Freezeframing for speed boosts. [start, end], replacing the frame with the start frame.
freeze_ranges: list[list[int]] = [
    [],
    []
]

# Zones for the encoder.
zones: dict[tuple[int, int], dict[str, Any]] = {
    (8732, 9019): {'q': 14},
}


def filterchain(clip: vs.VideoNode) -> vs.VideoNode | tuple[vs.VideoNode]:
    import lvsfunc as lvf
    import vardefunc as vdf
    from awsmfunc import bbmod
    from debandshit import dumb3kdb
    from havsfunc import FastLineDarkenMOD  # type:ignore
    from stgfunc import SetsuCubic
    from vsdehalo import dehalo_alpha, fine_dehalo
    from vsdenoise import CCDPoints, MVTools, PelType, ccd, prefilter_to_full_range
    from vsrgtools import contrasharpening_dehalo
    from vsscale import DPID
    from vstools import depth, get_neutral_value

    clip = vdf.initialise_clip(clip)

    # Edgefixing. Inconsistent, and I can't be bothered to scenefilter rekt, so just using bbmod.
    bb = bbmod(clip, 3, 3, 3, 3, planes=[0])

    # Dehaloing/Edgecleaning. Can't protect the credits easily unfortunately, but oh well. BD worry.
    with vdf.YUVPlanes(bb) as planes:
        alpha = dehalo_alpha(planes.Y, rx=2.2, ry=2.2, ss=1)
        planes.Y = fine_dehalo(alpha, rx=2.8, ry=2.8, brightstr=0.80, lowsens=30, highsens=80, thma=200, thmi=20, ss=1)

    dehalo = planes.clip  # Strong edgecleaning because it's so starved, warping's necessary to deal with compression
    csharp_dehalo = contrasharpening_dehalo(dehalo, bb, level=0.4)

    # Downscaling to 1080p. The downscale leaves the lines a bit brighter than Abema, so doing some line darkening.
    down = DPID(sigma=0.5, scaler=SetsuCubic()).scale(csharp_dehalo, 1920, 1080)
    darken = FastLineDarkenMOD(down, strength=12)

    # Denoising. I'll worry more about potential detail loss come BDs.
    mv = MVTools(darken, tr=3, refine=4, pel_type=PelType.WIENER)
    mv.analyze()
    degrain = mv.degrain(thSAD=65)

    ccd_uv = ccd(degrain, thr=4, tr=3, ref_points=CCDPoints.ALL)

    # Debanding. Masked and rather weak, as the strong static grain will hide most banding anyway.
    boost = prefilter_to_full_range(ccd_uv, 4)
    detail_mask = lvf.mask.detail_mask_neo(boost, sigma=2, detail_brz=0.007, lines_brz=0.015)

    deband = dumb3kdb(ccd_uv, radius=18, threshold=[16, 12])
    deband_masked = core.std.MaskedMerge(deband, ccd_uv, detail_mask)

    # Cleaning up bright areas to further save space.
    decs = vdf.decsiz(deband_masked, min_in=208 << 8, max_in=240 << 8,
                      blur_method=vdf.BilateralMethod.BILATERAL_GPU_RTC)

    # Freezeframing to save space and time.
    freeze = decs.std.FreezeFrames(freeze_ranges[0], freeze_ranges[1], freeze_ranges[0])

    # Graining. Static because C2C has this strong static grain pattern over some shows (see also: Majo no Tabitabi).
    freeze = depth(freeze, 10)

    grain = lvf.chickendream(
        freeze, rad=0.004, res=int(get_neutral_value(freeze)), draft=True, luma_scaling=8, cf=True
    )

    return grain


FILTERED = filterchain(BGLOBAL.clip_cut)


def post_filterchain(path: str) -> vs.VideoNode:
    """Pasta's system is super slow when running both VS and x265 at the same time, so splitting the load."""
    import lvsfunc as lvf

    src = lvf.src(path)
    flt = cast(vs.VideoNode, FILTERED[0])

    return src.std.CopyFrameProps(flt)


if __name__ == "__main__":
    from project_module import test

    runner = vse.EncodeRunner(ABEMA, cast(vs.VideoNode, FILTERED))
    runner.video(zones=zones)
    runner.lossless(post_filterchain=post_filterchain)  # type:ignore
    runner.audio(external_audio_file=test.process_audio(__file__))
    runner.mux("LightArrowsEXE@Kaleido")
    runner.run()
elif __name__ == "__vapoursynth__":
    if not isinstance(FILTERED, vs.VideoNode):
        raise vs.Error(f"Input clip has multiple output nodes ({len(FILTERED)})! "
                       "Please output a single clip")
    else:
        vse.video.finalize_clip(FILTERED).set_output(0)
else:
    ABEMA.clip_cut.set_output(0)

    if not isinstance(FILTERED, vs.VideoNode):
        for i, clip_filtered in enumerate(FILTERED, start=1):
            clip_filtered.set_output(i)
    else:
        FILTERED.set_output(1)

    # for i, audio_node in enumerate(DVD.audios_cut, start=10):
    #     audio_node.set_output(i)
