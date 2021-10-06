from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import vapoursynth as vs
from lvsfunc.types import Matrix
from vardautomation import FileInfo
from vsutil import (Range, depth, get_depth, get_w, get_y, iterate, join,
                    plane, split)

from .util import _get_bits

core = vs.core


def rescaler(clip: vs.VideoNode, height: int,
             shader_file: Optional[str] = None, **kwargs: Any
             ) -> Tuple[vs.VideoNode, vs.VideoNode]:
    """
    Multi-descaling + reupscaling function.
    Compares multiple descales and takes darkest/brightest pixels from clips as necessary
    """
    import lvsfunc as lvf
    import muvsfunc as muf
    from vardefunc.mask import FDOG
    from vardefunc.scale import fsrcnnx_upscale, nnedi3_upscale

    bits = get_depth(clip)
    clip = depth(clip, 32)

    clip_y = get_y(clip)
    scalers: List[Callable[[vs.VideoNode, int, int], vs.VideoNode]] = [
        lvf.kernels.Spline36().descale,
        lvf.kernels.Catrom().descale,
        lvf.kernels.BicubicSharp().descale,
        lvf.kernels.Catrom().scale
    ]

    descale_clips = [scaler(clip_y, get_w(height), height) for scaler in scalers]

    descale_clip = core.std.Expr(descale_clips, 'x y z a min max min y z a max min max z a min max')
    if shader_file:
        rescale = fsrcnnx_upscale(descale_clip, shader_file=shader_file, downscaler=None)
    else:
        rescale = nnedi3_upscale(descale_clip)

    rescale = muf.SSIM_downsample(rescale, clip.width, clip.height, smooth=((3 ** 2 - 1) / 12) ** 0.5,
                                  sigmoid=True, filter_param_a=0, filter_param_b=0)

    l_mask = FDOG().get_mask(clip_y, lthr=0.065, hthr=0.065).std.Maximum().std.Minimum()
    l_mask = l_mask.std.Median().std.Convolution([1] * 9)  # stolen from varde xd
    masked_rescale = core.std.MaskedMerge(clip_y, rescale, l_mask)

    scaled = join([masked_rescale, plane(clip, 1), plane(clip, 2)])

    upscale = lvf.kernels.Spline36().scale(descale_clips[0], clip.width, clip.height)
    detail_mask = lvf.scale.descale_detail_mask(clip_y, upscale, threshold=0.04)

    scaled_down = scaled if bits == 32 else depth(scaled, bits)
    mask_down = detail_mask if bits == 32 else depth(detail_mask, 16, range_in=Range.FULL, range=Range.LIMITED)
    return scaled_down, mask_down


def to_rgbs(clip: vs.VideoNode, matrix: int = 1) -> vs.VideoNode:
    clip = depth(clip, 32).std.SetFrameProp('_Matrix', intval=matrix)
    clip = core.resize.Bicubic(clip, format=vs.RGBS)
    return clip


def to_yuvp16(clip: vs.VideoNode, matrix: int = 1) -> vs.VideoNode:
    return core.resize.Bicubic(clip, format=vs.YUV420P16, matrix=matrix)


def detail_mask(clip: vs.VideoNode,
                sigma: float = 1.0, rxsigma: List[int] = [50, 200, 350],
                pf_sigma: Optional[float] = 1.0,
                rad: int = 3, brz: Tuple[int, int] = (2500, 4500),
                rg_mode: int = 17,
                ) -> vs.VideoNode:
    """
    A detail mask aimed at preserving as much detail as possible within darker areas,
    even if it contains mostly noise.
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
    # blur_ret_brz = core.morpho.Close(blur_ret_brz, size=8)

    kirsch_mask = kirsch(clip_y).std.Binarize(brz[1])
    kirsch_ifl = kirsch_mask.std.Deflate().std.Inflate()
    kirsch_brz = core.std.Binarize(kirsch_ifl, brz[1])
    # kirsch_brz = core.morpho.Close(kirsch_brz, size=4)

    merged = core.std.Expr([blur_ret_brz, kirsch_brz], "x y +")
    rm_grain = core.rgvs.RemoveGrain(merged, rg_mode)
    return rm_grain if bits == 16 else depth(rm_grain, bits)


def line_darkening(clip: vs.VideoNode, strength: float = 0.2, **kwargs: Any) -> vs.VideoNode:
    """
    Darken lineart through Toon.
    Taken from varde's repository.
    """
    from havsfunc import Toon

    darken = Toon(clip, strength, **kwargs)
    darken_mask = core.std.Expr(
        [core.std.Convolution(clip, [5, 10, 5, 0, 0, 0, -5, -10, -5], divisor=4, saturate=False),
         core.std.Convolution(clip, [5, 0, -5, 10, 0, -10, 5, 0, -5], divisor=4, saturate=False)],
        ['x y max {neutral} / 0.86 pow {peak} *'
            .format(neutral=1 << (clip.format.bits_per_sample-1),  # type: ignore[union-attr]
                    peak=(1 << clip.format.bits_per_sample)-1)])  # type: ignore[union-attr]
    return core.std.MaskedMerge(clip, darken, darken_mask)


def eedi3_singlerate_custom(clip: vs.VideoNode) -> vs.VideoNode:
    import lvsfunc as lvf

    eeargs: Dict[str, Any] = dict(field=0, dh=False, alpha=0.4, beta=0.6, gamma=30, nrad=2, mdis=30)
    nnargs: Dict[str, Any] = dict(field=0, dh=False, nsize=0, nns=4, qual=2)

    y = get_y(clip)
    return lvf.aa.eedi3(sclip=lvf.aa.nnedi3(**nnargs)(y), **eeargs)(y)


def transpose_sraa(clip: vs.VideoNode, **kwargs: Any) -> vs.VideoNode:
    import lvsfunc as lvf

    aa = lvf.sraa(clip.std.Transpose(), **kwargs)
    return lvf.sraa(aa.std.Transpose(), **kwargs)


def masked_f3kdb(clip: vs.VideoNode,
                 rad: int = 16,
                 thr: Union[int, List[int]] = 24,
                 grain: Union[int, List[int]] = [12, 0],
                 mask_args: Dict[str, Any] = {}
                 ) -> vs.VideoNode:
    """Basic f3kdb debanding with detail mask"""
    from debandshit import dumb3kdb

    deb_mask_args: Dict[str, Any] = dict(brz=(1000, 2750))
    deb_mask_args |= mask_args

    bits, clip = _get_bits(clip)

    deband_mask = detail_mask(clip, **deb_mask_args)

    deband = dumb3kdb(clip, radius=rad, threshold=thr, grain=grain)
    deband_masked = core.std.MaskedMerge(deband, clip, deband_mask)
    deband_masked = deband_masked if bits == 16 else depth(deband_masked, bits)
    return deband_masked


def masked_placebo(clip: vs.VideoNode,
                   rad: int = 12, thr: Union[int, List[int]] = 4,
                   itr: int = 2, grain: int = 2,
                   mask_args: Dict[str, Any] = {}
                   ) -> vs.VideoNode:
    """Basic placebo debanding with detail mask"""
    deb_mask_args: Dict[str, Any] = dict(brz=(2250, 4500))
    deb_mask_args |= mask_args

    bits, clip = _get_bits(clip)

    deband_mask = detail_mask(clip, **deb_mask_args)

    deband = placebo_debander(clip, radius=rad, threshold=thr, grain=grain, iterations=itr)
    deband_masked = core.std.MaskedMerge(deband, clip, deband_mask)
    deband_masked = deband_masked if bits == 16 else depth(deband_masked, bits)
    return deband_masked


def placebo_debander(clip: vs.VideoNode, grain: int = 4, **deband_args: Any) -> vs.VideoNode:
    return join([  # Still not sure why splitting it up into planes is faster, but hey! It works!
        core.placebo.Deband(plane(clip, 0), grain=grain, **deband_args),
        core.placebo.Deband(plane(clip, 1), grain=0, **deband_args),
        core.placebo.Deband(plane(clip, 2), grain=0, **deband_args)
    ])


def generate_comparison(src: FileInfo, enc: vs.VideoNode, **args: Any) -> None:
    from vardautomation import make_comps

    make_comps(
        {
            'source': src.clip_cut,
            'filtered': enc,
        },
        num=int(src.clip_cut.num_frames / 500) if src.clip_cut.num_frames > 5000 else 80,
        collection_name=f'{src.name} Encode (autogenerated comp)',
        path=f'.comps/{src.name}', force_bt709=True, slowpics=True, public=False, **args
    )


def prot_dpir(clip: vs.VideoNode, strength: int = 25,
              matrix: Optional[Union[Matrix, int]] = None,
              cuda: bool = True, device_index: int = 0,
              **dpir_args: Any) -> vs.VideoNode:
    """
    Protective DPIR function for the deblocking mode.
    Sometimes vs-dpir's deblocking mode will litter a random frame with a lot of red dots.
    This is obviously undesirable, so this function was written to combat that.
    Original code by Zewia, modified by LightArrowsEXE.
    Dependencies:
    * vs-dpir
    :param clip:            Input clip
    :param strength:        DPIR's deblocking strength
    :param matrix:          Enum for the matrix of the input clip. See ``types.Matrix`` for more info.
                            If `None`, gets matrix from the "_Matrix" prop of the clip
    :param cuda:            Device type used for deblocking. Uses CUDA if True, else CPU
    :param device_index:    The 'device_index' + 1º device of type device type in the system
    :dpir_args:             Additional args to pass onto DPIR
    :return:                Deblocked clip
    """
    from vsdpir import DPIR

    if clip.format is None:
        raise ValueError("prot_dpir: 'Variable-format clips not supported'")

    dpir_args |= dict(strength=strength, task='deblock',
                      device_type='cuda' if cuda else 'cpu',
                      device_index=device_index)

    clip_rgb = depth(clip, 32).std.SetFrameProp('_Matrix', intval=matrix)
    clip_rgb = core.resize.Bicubic(clip_rgb, format=vs.RGBS)

    debl = DPIR(clip_rgb, **dpir_args)
    rgb_planes = split(debl)

    # Grab the brigher parts of the R plane to avoid model fuckery
    # Everything below 5 (8 bit value) gets replaced with the ref's R plane
    rgb_planes[0] = core.std.Expr([rgb_planes[0], rgb_planes[1], plane(clip_rgb, 0)],
                                  'z x > y 5 255 / <= and z x ?')
    rgb_merge = join(rgb_planes, family=vs.RGB)

    return core.resize.Bicubic(rgb_merge, format=clip.format.id, matrix=matrix)
