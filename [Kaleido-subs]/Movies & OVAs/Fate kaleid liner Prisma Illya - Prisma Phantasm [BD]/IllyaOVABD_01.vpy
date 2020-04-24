import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import havsfunc as haf
import mvsfunc as mvf
import debandshit as ds
import atomchtools as at
import awsmfunc as awsm
from toolz import functoolz
from nnedi3_resample import nnedi3_resample
from descale import get_filter
from vsTAAmbk import TAAmbk
from vsutil import *
core = vs.core
core.max_cache_size = 128000
core.num_threads = 36


def _descaler(clip: vs.VideoNode, h: int = 720, kernel: str = 'bicubic',
                  b: float = 0, c: float = 0.5, taps: int = 4) -> vs.VideoNode:
    desc = get_filter(b, c, taps, kernel)(clip, get_w(h), h)
    upsc = nnedi3_resample(desc, clip.width, clip.height, kernel='gauss', invks=True,
                           invkstaps=2, taps=1, a1=32, nns=4, qual=2, pscrn=4)
    mask = fvf.Depth(at.DiffRescaleMask(fvf.Depth(clip, 8), h,
                     kernel=kernel, b=b, c=c, taps=taps), 32)
    return core.std.MaskedMerge(upsc, clip, mask)


@functoolz.curry
def _unsharp(clip: vs.VideoNode, strength: float = 1.0) -> vs.VideoNode:
    planes = split(clip)
    l_mask = fvf.Depth(kgf.retinex_edgemask(fvf.Depth(planes[0], 16)), 32)
    blurred_clip = core.std.Convolution(planes[0], matrix=[1, 2, 1, 2, 4, 2, 1, 2, 1])
    unsharp = core.std.Expr(clips=[planes[0], blurred_clip], expr=['x y - ' + str(strength) + ' * x +'])
    planes[0] = core.std.MaskedMerge(planes[0], unsharp, l_mask)
    return join(planes).rgsf.Repair(clip, 13)


@functoolz.curry
def _fix_lineart(clip: vs.VideoNode) -> vs.VideoNode:
    if get_depth(clip) != 16:
        clip, clip_c = fvf.Depth(clip, 16), clip
    dehalo = haf.FineDehalo(clip, rx=2.8, thmi=91, thma=128, darkstr=0.3, brightstr=1, contra=1)
    dering = haf.EdgeCleaner(dehalo, strength=1, rmode=13, smode=1, hot=True)
    return fvf.Depth(dering, get_depth(clip_c))


@functoolz.curry
def _denoise(clip: vs.VideoNode) -> vs.VideoNode:
    denY = core.knlm.KNLMeansCL(clip, d=2, a=3, h=0.6)
    return fvf.Depth(core.knlm.KNLMeansCL(clip, d=2, a=3, h=1, channels="UV"), 16)


@functoolz.curry
def _dark_aa(clip: vs.VideoNode) -> vs.VideoNode:
    if get_depth(clip) != 16:
        clip, clip_c = fvf.Depth(clip, 16), clip
    darken = haf.FastLineDarkenMOD(clip, strength=24, protection=6, luma_cap=235)
    return fvf.Depth(TAAmbk(darken, aatype='Eedi3', repair=12, opencl=True), get_depth(clip_c))

@functoolz.curry
def _denoiseNgrain(clip: vs.VideoNode, src: vs.VideoNode) -> vs.VideoNode:
    m_denoised = core.knlm.KNLMeansCL(clip, h=1)
    maska = fvf.Depth(ds.rangemask(get_y(fvf.Depth(m_denoised, 16)), 3, 2), 32).std.Binarize(0.2)
    maskb = get_y(clip).std.Prewitt().std.Binarize(0.045)
    mask = core.std.Expr([maska, maskb], 'x y max').rgsf.RemoveGrain(22).rgsf.RemoveGrain(11)

    deband = core.placebo.Deband(clip, planes=1, threshold=5, radius=20, iterations=2)
    deband = core.placebo.Deband(deband, planes=2|4, threshold=3, grain=0)
    deband = core.std.MaskedMerge(deband, clip, mask)

    return kgf.adaptive_grain(deband, 0.2, luma_scaling=6)


opstart = 2789

op_range      = [(opstart,opstart+2157)]
ed_range      = [(84721,87043),(89166,89422)]
descale_old   = [(4947,5336),(22569,22958)]
descale_810   = [(49179,53688)]


src_a = lvf.src(r"BDMV/[BDMV][191127] Fate／kaleid liner Prisma☆Illya Prisma☆Phantasm/PRISMAPHANTASM_SP/BDMV/STREAM/00001.m2ts")[48:-24]
src_b = lvf.src(r"BDMV/[BDMV][191127] Fate／kaleid liner Prisma☆Illya Prisma☆Phantasm/PRISMAPHANTASM_SP/BDMV/STREAM/00004.m2ts")[24:-24]
src = src_a+src_b
ef = awsm.bbmod(src, 1, 1, 1, 1, thresh=35, blur=999, y=True, u=False, v=False, scale_thresh=True)
limit = core.std.Limiter(ef, 16, [235,240])
ef = fvf.Depth(limit, 32)


h = [720, 810]
planes = split(ef) # Ranges and descale kernels courtesy of Varde's detective work (mostly)
l_mask = fvf.Depth(kgf.retinex_edgemask(fvf.Depth(planes[0], 16)), 32)
descaled = lvf.rfs(_descaler(planes[0], h[0], kernel='bilinear'),
                   _descaler(planes[0], h[0], kernel='bicubic', b=0, c=.5),
                   ranges = descale_old)
descaled = lvf.rfs(descaled,
                   _descaler(planes[0], h[1], kernel='spline36'),
                   ranges = descale_810)
descaled = lvf.rfs(descaled, planes[0], op_range)
planes[0] = core.std.MaskedMerge(planes[0], descaled, l_mask)
scaled = join(planes)


filter_chain = functoolz.compose(_denoise, _unsharp(strength=0.25), _fix_lineart, _dark_aa, _denoiseNgrain(src=ef))
main_filter = filter_chain(scaled) # Currying is actually pretty neat, ngl

merge = lvf.rfs(main_filter,
                fvf.Depth(src, get_depth(main_filter)),
                ed_range)


out = merge
final = fvf.Depth(out, 10)
final.set_output()
