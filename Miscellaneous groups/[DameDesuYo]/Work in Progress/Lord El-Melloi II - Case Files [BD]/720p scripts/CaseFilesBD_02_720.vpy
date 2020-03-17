from typing import Callable, TypeVar, Union, List, Tuple, Optional
import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import havsfunc as haf
from vsTAAmbk import TAAmbk
from cooldegrain import *
from vsutil import *
core = vs.core


def create_dmask(clip: vs.VideoNode, luma_scaling: float, depth: Optional[int] = None) -> vs.VideoNode:
    if depth:
        clip = fvf.Depth(clip, depth)
    return core.adg.Mask(clip.std.PlaneStats(), luma_scaling)


def adap_denoise(clip: vs.VideoNode, luma_scaling: float, depth: int) -> vs.VideoNode:
    d_mask = create_dmask(clip, luma_scaling, depth)
    denoise_a = CoolDegrain(clip, tr=1, thsad=72, thsadc=48, bits=depth, blksize=8, overlap=4)
    denoise_b = CoolDegrain(clip, tr=1, thsad=24, thsadc=48, bits=depth, blksize=8, overlap=4)
    return core.std.MaskedMerge(denoise_a, denoise_b, d_mask)


def masked_aa(clip: vs.VideoNode, strength: float) -> vs.VideoNode:
    l_mask = kgf.retinex_edgemask(denoise).std.Maximum()
    return lvf.nneedi3_clamp(denoise, mask=l_mask, strength=strength)


def interp_aa(clip: vs.VideoNode, strength: float, mappings: str, ) -> vs.VideoNode:
    l_mask = kgf.retinex_edgemask(clip).std.Maximum()
    b_mask = core.std.Binarize(get_y(clip), 0.3).std.Invert()
    mask = core.std.Expr([l_mask, b_mask], "x y -").std.Maximum().std.Inflate()

    aa = TAAmbk(clip, aatype='Eedi3', mclip=mask, cycle=1)
    aa = core.std.MaskedMerge(aa, haf.QTGMC(aa, InputType=1, TR2=3), mask)
    return fvf.rfs(masked_aa(clip, strength), aa, mappings=mappings)


def adap_deband(clip: vs.VideoNode, luma_scaling: float) -> vs.VideoNode:
    if clip.format.bits_per_sample != 16:
        raise ValueError(f"Clip needs to be 16 bit, not {clip.format.bits_per_sample}!")
    d_mask = create_dmask(clip, luma_scaling)
    deband_a = core.f3kdb.Deband(clip, range=16, y=56, cb=48, cr=48, grainy=32, grainc=0, output_depth=get_depth(clip))
    deband_b = core.f3kdb.Deband(clip, range=14, y=40, cb=32, cr=32, grainy=32, grainc=0, output_depth=get_depth(clip))
    return core.std.MaskedMerge(deband_a, deband_b, fvf.Depth(d_mask, get_depth(clip)))


def grain_it(clip: vs.VideoNode,
             avar: float, var: float, luma_scaling: float, constant: bool,
             mappings: Optional[str] = None) -> vs.VideoNode:
    grain_a = kgf.adaptive_grain(deband, avar, luma_scaling=luma_scaling)
    if mappings is None:
        return grain_a
    grain_b = core.grain.Add(deband, var=var, uvar=0, constant=constant)
    return fvf.rfs(grain_a, grain_b, mappings=mappings)


opstart = 1966


op_grain = f"[{opstart+285} {opstart+573}]" if opstart else ""


src = lvf.src(r'../BDMV/[BDMV] Lord El-Melloi II-sei no Jikenbo ~Rail Zeppelin Grace Note~ [Vol.02]/BDROM',
              mpls=True, mpls_playlist=0)
src = src[24:34791]
ef = lvf.edgefixer(src, [1,0,0])
ef = fvf.Depth(ef, 32)

descaled = kgf.inverse_scale(ef, height=720,
                             kernel='bicubic', b=0, c=1/2,
                             mask_detail=True)


denoise = adap_denoise(descaled, luma_scaling=6, depth=16)
aa = interp_aa(denoise, strength=1.7, mappings="[16987 17076] [17248 17345] [18328 18435] [21056 21100]")
deband = adap_deband(aa, luma_scaling=6)
grain = grain_it(deband, avar=.15, var=3, luma_scaling=6, constant=False,
                 mappings=op_grain)


out = grain
final = fvf.Depth(out, 10)
final.set_output()
