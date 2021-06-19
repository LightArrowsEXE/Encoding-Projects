"""
    Generic filtering.
    Sticking all the common filtering in here means I have to do less updating to invidiual scripts, yay.
"""
from typing import Any, Dict, List, Optional, Tuple, Union

import vapoursynth as vs
from vsutil import depth, get_y, iterate

core = vs.core


def rescaler(clip: vs.VideoNode, height: int) -> Tuple[vs.VideoNode, vs.VideoNode]:
    """
    Basic rescaling and mask generating function using nnedi3.
    """
    from lvsfunc.kernels import Bicubic
    from lvsfunc.scale import descale_detail_mask
    from vardefunc.mask import FDOG
    from vardefunc.scale import nnedi3_upscale
    from vsutil import get_w, join, plane, Range

    bits, clip = _get_bits(clip, expected_depth=32)

    clip_y = get_y(clip)
    descale = Bicubic().descale(clip_y, get_w(height, clip.width/clip.height), height)
    rescale = Bicubic().scale(nnedi3_upscale(descale, pscrn=1), clip.width, clip.height)

    l_mask = FDOG().get_mask(clip_y, lthr=0.065, hthr=0.065).std.Maximum().std.Minimum()
    l_mask = l_mask.std.Median().std.Convolution([1] * 9)  # stolen from varde xd
    masked_rescale = core.std.MaskedMerge(clip_y, rescale, l_mask)

    scaled = join([masked_rescale, plane(clip, 1), plane(clip, 2)])

    upscale = Bicubic().scale(descale, 1920, 1080)
    detail_mask = descale_detail_mask(clip_y, upscale, threshold=0.045)

    scaled_down = scaled if bits == 32 else depth(scaled, bits)
    mask_down = detail_mask if bits == 32 else depth(detail_mask, 16, range_in=Range.FULL, range=Range.LIMITED)
    return scaled_down, mask_down


def detail_mask(clip: vs.VideoNode,
                sigma: float = 1.0, rxsigma: List[int] = [50, 200, 350],
                pf_sigma: Optional[float] = 1.0,
                rad: int = 3, brz: Tuple[int, int] = (2500, 4500),
                rg_mode: int = 17,
                ) -> vs.VideoNode:
    """
    A detail mask aimed at preserving as much detail as possible
    within darker areas, even if it contains mostly noise.
    """
    from kagefunc import kirsch

    bits, clip = _get_bits(clip)

    clip_y = get_y(clip)
    pf = core.bilateral.Gaussian(clip_y, sigma=pf_sigma) if pf_sigma else clip_y
    ret = core.retinex.MSRCP(pf, sigma=rxsigma, upper_thr=0.005)

    blur_ret = core.bilateral.Gaussian(ret, sigma=sigma)
    blur_ret_diff = core.std.Expr([blur_ret, ret], "x y -")
    blur_ret_dfl = core.std.Deflate(blur_ret_diff)
    blur_ret_ifl = iterate(blur_ret_dfl, core.std.Inflate, 4)
    blur_ret_brz = core.std.Binarize(blur_ret_ifl, brz[0])
    blur_ret_brz = core.morpho.Close(blur_ret_brz, size=8)

    kirsch_mask = kirsch(clip_y).std.Binarize(brz[1])
    kirsch_ifl = kirsch_mask.std.Deflate().std.Inflate()
    kirsch_brz = core.std.Binarize(kirsch_ifl, brz[1])
    kirsch_brz = core.morpho.Close(kirsch_brz, size=4)

    merged = core.std.Expr([blur_ret_brz, kirsch_brz], "x y +")
    rm_grain = core.rgvs.RemoveGrain(merged, rg_mode)
    return rm_grain if bits == 16 else depth(rm_grain, bits)


def denoising(clip: vs.VideoNode,
              bm3d_sigma: Union[float, List[float]] = 0.5, bm3d_rad: int = 2,
              dec_sigma: float = 8.0, dec_min: int = 192 << 8, dec_max: int = 232 << 8,
              SMD_args: Dict[str, Any] = {}) -> vs.VideoNode:
    from havsfunc import SMDegrain
    from lvsfunc.denoise import bm3d
    from vardefunc.noise import decsiz

    bits, clip = _get_bits(clip)

    ref_args: Dict[str, Any] = dict(tr=3, thSAD=150, thSADC=200, contrasharp=16, pel=4, subpixel=3)
    ref_args |= SMD_args

    ref = SMDegrain(clip, **ref_args)
    denoise = bm3d(clip, sigma=bm3d_sigma, radius=bm3d_rad, ref=ref)
    decs = decsiz(denoise, sigmaS=dec_sigma, min_in=dec_min, max_in=dec_max)
    return decs if bits == 16 else depth(decs, bits)


def antialiasing(clip: vs.VideoNode, strength: float = 1.4) -> vs.VideoNode:
    from lvsfunc.aa import clamp_aa, nneedi3_clamp, upscaled_sraa

    bits, clip = _get_bits(clip)

    aa_weak = nneedi3_clamp(clip)
    aa_str = upscaled_sraa(clip)
    aa_clamped = clamp_aa(clip, aa_weak, aa_str, strength=strength)
    return aa_clamped if bits == 16 else depth(aa_clamped, bits)


def debanding(clip: vs.VideoNode) -> vs.VideoNode:
    from vardefunc.deband import dumb3kdb

    bits, clip = _get_bits(clip)

    deband_mask = detail_mask(clip, brz=(1000, 2750))

    deband = dumb3kdb(clip, radius=18, threshold=[40, 64], grain=[12, 24])  # Heavy chroma banding
    deband_masked = core.std.MaskedMerge(deband, clip, deband_mask)
    return deband_masked if bits == 16 else depth(deband_masked, bits)


# Helpers
def _get_bits(clip: vs.VideoNode, expected_depth: int = 16) -> Tuple[int, vs.VideoNode]:
    from vsutil import get_depth

    bits = get_depth(clip)
    return bits, depth(clip, expected_depth) if bits != expected_depth else clip
