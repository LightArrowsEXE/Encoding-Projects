"""
Entire filter chain here, since we're reusing this for every single script, and being anti-redundancy is fun.
"""
import vapoursynth as vs

from .filters import antialiasing, debanding, denoising, rescaler

core = vs.core


def filterchain(clip: vs.VideoNode) -> vs.VideoNode:
    from adptvgrnMod import adptvgrnMod
    from vsutil import depth

    clip16 = depth(clip, 16)

    scaled, credit_mask = rescaler(clip16, height=844)
    denoise = denoising(scaled)
    aa_clamped = antialiasing(denoise)

    credits_merged = core.std.MaskedMerge(aa_clamped, depth(clip16, 16), credit_mask)

    deband = debanding(credits_merged)
    grain = adptvgrnMod(deband, strength=0.3, luma_scaling=10, size=1.25, sharp=100,
                        grain_chroma=False, static=False, seed=42069)

    return depth(grain, 10)
