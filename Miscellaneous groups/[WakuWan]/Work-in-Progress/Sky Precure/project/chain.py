import inspect
import warnings
from typing import cast

from vstools import FrameRangesN, core, vs

__all__: list[str] = [
    "filtering",
    "post_filterchain",
]

def filtering(clip: vs.VideoNode, draft: bool = False, filename: str | None = None,
              check_amz: bool = False, replace_cr: FrameRangesN = [], diff_amz: bool = False,
              check_dh: bool = False, dh_show_mask: bool = False, show_error_mask: bool = False
              ) -> vs.VideoNode | tuple[vs.VideoNode, ...]:
    from functools import partial
    from pathlib import Path

    import lvsfunc as lvf  # noqa type:ignore
    from vsaa import Nnedi3, based_aa
    from vsdeband import F3kdb, Placebo, sized_grain
    from vsdehalo import fine_dehalo
    from vsdenoise import nl_means
    from vskernels import Lanczos
    from vsrgtools import bilateral, contrasharpening, lehmer_diff_merge
    from vsscale import SSIM, MergedFSRCNNX, descale, descale_detail_mask
    from vstools import LengthRefClipMismatchError, initialize_clip, replace_ranges

    from project import dehardsubber

    assert clip.format

    if draft:
        return clip

    if not filename:
        frame = inspect.stack()[1]
        module = inspect.getmodule(frame[0])
        filename = str(module.__file__)  # type:ignore

    kf = Path(f"assets/{Path(filename).stem}.txt")

    if not kf.exists():
        from vstools import Keyframes

        print(f"Keyframes not found; generating... Import this kf file ({kf}) into vspreview.")
        kf.parents[0].mkdir(parents=True, exist_ok=True)
        Keyframes.from_clip(clip).to_file(kf)

    clip = initialize_clip(clip)

    # Merging with amazon to fix up a lot of compression issues.
    amz_paths = Path('src/').glob(f'*{Path(filename).stem.split("_")[-1]}*Amazon*.mkv.dgi')
    amz = tuple([lvf.src(x, clip)[360:] for x in amz_paths])

    if not amz:
        warnings.warn("No amazon videos found! Please fix!")
        exit()

    if check_amz:
        print(amz_paths)
        return amz

    for x in amz:
        LengthRefClipMismatchError(filtering, clip, x)

    if diff_amz:
        return lvf.diff(clip, amz[0], thr=48)  # type:ignore[return-value]

    merged = lehmer_diff_merge(clip, *amz, filter=partial(bilateral, sigmaR=11 / 255, gpu=False))
    merged = replace_ranges(merged, clip, replace_cr)

    # Dehardsubbing karaoke added by the merge.
    dehardsub = dehardsubber(merged, clip, dh_show_mask, top=890, bottom=16, left=24, right=24)

    if check_dh:
        return dehardsub

    # Mixed 900(/899.9?)/810, however any kernel seems to just add more error. Likely post-sharpened.
    # As-is, this is not cleanly rescaleable, but that might change with BDs?

    # ... but I need a mask for the credits, as this AA just nukes them.
    descaled = descale(
        fine_dehalo(dehardsub, rx=2.6, ss=1, pre_ss=2), height=[900, 810],
        kernels=Lanczos(5), upscaler=Lanczos(5), result=True,
        mask=partial(descale_detail_mask, thr=0.04, inflate=4)
    )

    if show_error_mask:
        return descaled.error_mask  # type:ignore[return-value]

    aa = based_aa(
        dehardsub, supersampler=MergedFSRCNNX(reference=Nnedi3(0)), downscaler=SSIM, rfactor=1.5
    )

    aa = core.std.MaskedMerge(aa, dehardsub, cast(vs.VideoNode, descaled.error_mask))

    # Pre-dehaloing to reduce the sharpening's negative effects somewhat.
    dehalo = fine_dehalo(aa, rx=2.8, ss=1, pre_ss=2)

    # Rather strong denoising to deal with the awful leftover ringing and ugly compression noise.
    debl = lvf.dpir(dehalo, strength=30)
    nlm = nl_means(debl, strength=[0.0, 0.65], tr=1, planes=[1, 2])

    # Debanding.
    f3kdb = F3kdb.deband(nlm, radius=17, thr=[40, 32])
    deband_csharp = contrasharpening(f3kdb, dehalo)

    # Graining.
    grain = sized_grain.adaptive(
        deband_csharp, [8.0, 0.35], luma_scaling=12.0, dynamic=True, grainer=Placebo, fade_edges=False,
        size=1.10, seed=69420, scaler=Lanczos(5), temporal_average=(35, 2)
    )

    return grain


def post_filterchain(path_to_lossless: str, ref: vs.VideoNode) -> vs.VideoNode:
    """Post filterchain to ensure necessary flags are properly set and to do some additional filtering."""
    from lvsfunc import source
    from vstools import CustomValueError, finalize_clip

    src = source(path_to_lossless)

    if ref is None:
       raise CustomValueError("You must pass a reference clip!")

    return finalize_clip(src.std.CopyFrameProps(ref[0]))
