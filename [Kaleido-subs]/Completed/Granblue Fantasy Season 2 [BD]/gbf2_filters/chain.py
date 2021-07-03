"""
Entire filter chain here, since we're reusing this for every single script, and being anti-redundancy is fun.
"""
import vapoursynth as vs

core = vs.core

from .filters import antialiasing, debanding, denoising, rescaler


def filterchain(clip: vs.VideoNode) -> vs.VideoNode:
    from adptvgrnMod import adptvgrnMod
    from vsutil import depth

    clip16 = depth(clip, 16)

    scaled, credit_mask = rescaler(clip16, height=844)
    denoise = denoising(scaled)
    aa_clamped = antialiasing(denoise)

    credits_merged = core.std.MaskedMerge(aa_clamped, depth(clip16, 16), credit_mask)

    deband = debanding(credits_merged)
    grain = adptvgrnMod(deband, strength=0.3, luma_scaling=10, size=1.25, sharp=80, grain_chroma=False, seed=42069)

    return depth(grain, 10).std.Limiter(16 << 2, [235 << 2, 240 << 2], [0, 1, 2])
