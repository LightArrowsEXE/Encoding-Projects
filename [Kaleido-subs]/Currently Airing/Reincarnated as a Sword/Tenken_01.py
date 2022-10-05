from typing import Any, cast

import vapoursynth as vs
import vsencode as vse

from project_module import test

ini = vse.generate.init_project("x265")
core = vs.core
run = __name__ in ('__vapoursynth__', '__main__')

BILI = vse.FileInfo("src/Tensei shitara Ken Deshita - 01 - 2160p WEB H.264 -NanDesKa (B-Global).mkv", (None, None))  # noqa
ABEMA = vse.FileInfo("src/[NICE SIMULCAST HIDIVE] Tensei Shitara Ken Deshita (Reincarnated as a Sword) - 01.mkv", (None, None))  # noqa


# Scenefiltering
opstart: int | None = None
edstart: int | None = None
op_offset: int = 1
ed_offset: int = 1

# Freezeframing for speed boosts. [start, end], replacing the frame with the start frame.
freeze_ranges: list[list[int]] = [
    [813, 1934, 2128, 2162, 2237, 2688, 2760, 2812, 2957, 3085],
    [863, 2004, 2161, 2212, 2302, 2724, 2793, 2836, 3070, 3155]
]

# Zones for the encoder.
zones: dict[tuple[int, int], dict[str, Any]] = {}


# OP/ED scenefiltering
if opstart is not None:
    ...

if edstart is not None:
    ...


def filterchain(clip: vs.VideoNode, ref: vs.VideoNode) -> vs.VideoNode | tuple[vs.VideoNode]:
    import lvsfunc as lvf
    import vardefunc as vdf
    from awsmfunc import bbmod
    from debandshit import dumb3kdb
    from vsaa import Nnedi3SS
    from vsdehalo import dehalo_alpha, edge_cleaner
    from vsdenoise import MVTools, PelType, prefilter_to_full_range  # type:ignore
    from vskernels import Catrom, Point
    from vsrgtools import contrasharpening, lehmer_diff_merge
    from vsscale import ssim_downsample

    class NoShiftCatrom(Catrom):
        def shift(self, clip, *args, **kwargs):
            return clip

    # Checking for diffs between sources before filtering.
    # return lvf.diff(clip.resize.Bicubic(ref.width, ref.height), ref, thr=96)

    down = ssim_downsample(clip, 1920, 1080)
    merged = lehmer_diff_merge(down, ref)

    # Credits differ between sources. Abema is probs more up-to-date, but the video quality is too bad to splice as-is.
    merged = lvf.rfs(merged, down, [(120, 203), (33351, 33482)])

    clip = vdf.initialise_clip(merged)

    # Edgefixing. Inconsistent, and I can't be bothered to scenefilter rekt, so just using bbmod.
    bb = bbmod(clip, 1, 1, 1, 1, planes=[0])

    # Denoising. This is pretty strong, but I can worry about potential detail loss come BDs.
    # This getup doesn't harm static grain much anyway, so it's largely fine.
    dpir = lvf.dpir(bb, strength=25, tiles=1 if run else 8, cuda='trt' if run else True)

    mv = MVTools(bb, prefilter=dpir, tr=3, refine=4, pel_type=PelType.WIENER)
    mv.analyze(dpir)
    degrain = mv.degrain(dpir, thSAD=80)

    csharp = contrasharpening(degrain, bb)

    # Dehaloing/Edgecleaning. Supersampling and "losslessly" (you get the idea) downsampling.
    with vdf.YUVPlanes(csharp) as planes:
        dehalo_ss = Nnedi3SS(field=0, shifter=NoShiftCatrom(), opencl=True) \
            .scale(planes.Y, planes.Y.width*2, planes.Y.height*2)
        alpha = dehalo_alpha(dehalo_ss, rx=2.2, ry=2.2, ss=1)
        ec = edge_cleaner(alpha, strength=7.5)
        planes.Y = Point().scale(ec, planes.Y.width, planes.Y.height)

    dehalo = planes.clip

    # Debanding. Masked and rather weak, as the strong static grain will hide most banding anyway.
    boost = prefilter_to_full_range(dehalo, 4)
    detail_mask = lvf.mask.detail_mask_neo(boost, sigma=2, detail_brz=0.007, lines_brz=0.015)

    deband = dumb3kdb(dehalo, radius=18, threshold=[24, 20])
    deband_masked = core.std.MaskedMerge(deband, dehalo, detail_mask)

    # Cleaning up bright areas to further save space.
    decs = vdf.decsiz(deband_masked, min_in=208 << 8, max_in=240 << 8)

    # Freezeframing to save space and time.
    freeze = decs.std.FreezeFrames(freeze_ranges[0], freeze_ranges[1], freeze_ranges[0])

    # Graining. Static because C2C has this strong static grain pattern over some shows (see also: Majo no Tabitabi).
    grain = lvf.chickendream(
        freeze, rad=0.004, res=255 << 8, draft=True, luma_scaling=10, cf=True
    )

    # Chickendream is so strong that it kinda kills the edges of some lines, hence csharpening.
    csharp_grain = contrasharpening(grain, decs)

    return csharp_grain


FILTERED = filterchain(BILI.clip_cut, ABEMA.clip_cut)


if __name__ == "__main__":
    runner = vse.EncodeRunner(ABEMA, cast(vs.VideoNode, FILTERED))
    runner.video(zones=zones)
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
