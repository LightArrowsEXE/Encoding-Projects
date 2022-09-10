from pathlib import Path
from typing import Any, cast

import vapoursynth as vs
import vsencode as vse

from project_module import filters, get_audio_paths

# import vstools as vst

ini = vse.generate.init_project("x265")
core = vse.util.get_vs_core(reserve_core=ini.reserve_core)
shader = vse.get_shader("FSRCNNX_x2_56-16-4-1.glsl")
run = __name__ in ('__vapoursynth__', '__main__')

SRC = vse.FileInfo("src/OP - Opening 20.dgi", (30, -30))
audio_paths = get_audio_paths(SRC.path.to_str(), return_glob=True)

# Zones for the encoder.
zones: dict[tuple[int, int], dict[str, Any]] = {}


def prefilter(clip: vs.VideoNode, draft: bool = False) -> vs.VideoNode | tuple[vs.VideoNode]:
    from lvsfunc import sivtc
    from vardefunc import initialise_clip

    # Simple, consistent pattern. TIVTC will likely still mess something up, so we're just keeping it straightforward.
    ivtc = sivtc(clip, 0)

    # Faster to process an 8bit clip than a 16bit one.
    if draft:
        return ivtc

    return initialise_clip(ivtc)


def filterchain(clip: vs.VideoNode) -> vs.VideoNode | tuple[vs.VideoNode]:
    from functools import partial

    import lvsfunc as lvf
    import vardefunc as vdf
    from awsmfunc import bbmod
    from debandshit import dumb3kdb, placebo_deband
    from havsfunc import QTGMC
    from stgfunc import Grainer, adaptive_grain
    from vsdehalo import HQDeringmod
    from vsdenoise import MVTools
    from vskernels import Bilinear, Catrom
    from vsmask.edge import FDoG
    from vsrgtools import contrasharpening, contrasharpening_dehalo
    from vsscale import descale
    from vstools import depth, get_y, scale_value

    # The lineart from the web version is actually better because the BDs were post-processed.
    # However, the compression fucks it over, and I can't salvage it. Sad!
    # Fix dirty edges.
    bb = bbmod(clip, 1, 1, 1, 1, blur=4, planes=[0])

    # Doing some weak deringing prior to descaling because it was introduced in the upscaled image.
    dering = HQDeringmod(bb.std.Limiter(), mthr=48, contra=False)
    dering = contrasharpening_dehalo(dering, clip)

    # Native 900p, likely either Bilinear or Catrom. 95% leaning woards Bilinear, but passing both to be safe.
    result = descale(depth(dering, 32), height=900, kernels=[Bilinear(), Catrom()], result=True,
                     upscaler=filters.shader_scaler(shader, strength=45))
    scaled, native_mask = map(partial(depth, bitdepth=16), [result.out, result.mask])

    # Chroma warping to fix the weird fuckery they did to the chroma edges. Contrasharpened to reduce damage caused.
    cwarp = scaled.warp.AWarpSharp2(thresh=88, blur=2, type=1, depth=6, planes=[1, 2])
    csharp = contrasharpening(cwarp, scaled, planes=[1, 2])

    # Motion interpolation for one singular cut. Severely limited to prevent causing much damage.
    l_mask = FDoG().edgemask(get_y(csharp), lthr=scale_value(0.03, 32, 16), hthr=scale_value(0.03, 32, 16))
    l_mask = l_mask.rgsf.RemoveGrain(4).std.Minimum().std.Deflate().std.Median().std.Convolution([1] * 9)

    interp = QTGMC(csharp, TFF=True, InputType=1, SourceMatch=3, TR0=2, TR1=2, TR2=3, Preset="Placebo",
                   ThSAD1=50, ThSAD2=50, Precise=False, opencl=True)
    interp = core.std.MaskedMerge(csharp, interp, l_mask)
    interp = lvf.rfs(csharp, interp, [(1168, 1201)])

    # Denoising. I know it's relatively strong, but there's really ugly blocking and compression noise all over.
    debl = lvf.dpir(interp, strength=30, cuda='trt' if run else True, tiles=1 if run else 8)

    mv = MVTools(interp, tr=3, prefilter=debl)
    mv.analyze(debl)
    degrain = mv.degrain(thSAD=125)

    cmerged = vdf.merge_chroma(degrain, debl)

    # Merging back native 1080p details.
    merge_native = core.std.MaskedMerge(cmerged, dering, native_mask)

    # Debanding. Weak lineart masking at most because it otherwise picks up too much junk I want debanded away.
    deband_wk = dumb3kdb(merge_native, radius=18, threshold=[24, 20])
    deband_wk = core.std.MaskedMerge(deband_wk, merge_native, l_mask)

    deband_str = placebo_deband(merge_native, iterations=2, threshold=6.0, grain=0)
    deband = lvf.rfs(deband_wk, deband_str, [(844, 874), (2786, 2825), (2944, 2949), (2993, 3032)])

    # Pre-graining.
    decs = vdf.decsiz(deband, min_in=192 << 8, max_in=240 << 8)

    # Finally, graining. Slightly stronger graining over specific scenes.
    grain = adaptive_grain(
        decs, [2.6, 0.35], luma_scaling=10, static=False, temporal_average=100,
        grainer=Grainer.AddNoise, size=2.0, type=3, every=2, seed=69420
    )

    grain_str = adaptive_grain(
        decs, [4.0, 0.35], luma_scaling=8, static=False, temporal_average=100,
        grainer=Grainer.AddNoise, size=3.5, type=3, every=2, seed=69420
    )

    grain = lvf.rfs(grain, grain_str, [(1202, 1448), (2253, 2395)])

    return grain


def post_filterchain(path: Path) -> vs.VideoNode:
    """Post-lossless encode to ensure we properly set the matrices and other props."""
    from lvsfunc import replace_ranges, source
    from vardefunc import initialise_clip

    src = source(path)

    # Grabbing the frameprops and sticking it on just the first frame for vsencode to read. Doing this on every frame
    # means running all the filtering from `filterchain` every single frame again, which is super slow.
    global FILTERED
    props = core.std.CopyFrameProps(src, FILTERED)
    src = replace_ranges(src, props, [0])

    return cast(vs.VideoNode, initialise_clip(src, 10))


PREFILTER = prefilter(SRC.clip_cut)
FILTERED = PREFILTER

if isinstance(PREFILTER, vs.VideoNode):
    FILTERED = filterchain(PREFILTER)


if __name__ == "__main__":
    runner = vse.EncodeRunner(SRC, cast(vs.VideoNode, FILTERED))
    runner.video(zones=zones, qp_clip=PREFILTER)
    runner.lossless(post_filterchain=post_filterchain)
    runner.audio("flac", external_audio_file=str(audio_paths[0]))
    runner.mux("LightArrowsEXE@Kaleido")
    runner.run()
elif __name__ == "__vapoursynth__":
    if not isinstance(FILTERED, vs.VideoNode):
        raise vs.Error(f"Input clip has multiple output nodes ({len(FILTERED)})! "
                       "Please output a single clip")
    else:
        vse.video.finalize_clip(FILTERED).set_output(0)
else:
    if isinstance(PREFILTER, vs.VideoNode):
        PREFILTER.set_output(0)
    else:
        SRC.clip_cut.set_output(0)
        FILTERED = PREFILTER

    if not isinstance(FILTERED, vs.VideoNode):
        for i, clip_filtered in enumerate(FILTERED, start=1):
            clip_filtered.set_output(i)
    else:
        FILTERED.set_output(1)

    # for i, audio_node in enumerate(DVD.audios_cut, start=10):
    #     audio_node.set_output(i)
