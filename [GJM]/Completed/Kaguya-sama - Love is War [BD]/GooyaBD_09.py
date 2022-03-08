import multiprocessing as mp
import os
from functools import partial
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union

import vapoursynth as vs
import yaml
from lvsfunc.misc import source
from lvsfunc.types import Range
from vardautomation import FileInfo, PresetAAC, PresetBD, VPath, get_vs_core
from vardefunc import initialise_input

from project_module import encoder as enc
from project_module import flt

with open("config.yaml", 'r') as conf:
    config = yaml.load(conf, Loader=yaml.FullLoader)

core = get_vs_core(range(0, (mp.cpu_count() - 2)) if config['reserve_core'] else None)


shader_file = 'assets/FSRCNNX_x2_56-16-4-1.glsl'
if not Path(shader_file).exists():
    hookpath = r"mpv/shaders/FSRCNNX_x2_56-16-4-1.glsl"
    shader_file = os.path.join(str(os.getenv("APPDATA")), hookpath)


# Sources
JP_BD = FileInfo(f"{config['bdmv_dir']}/かぐや様は告らせたい Vol.5/BD/BDMV/STREAM/00001.m2ts", (None, -25),
                 idx=lambda x: source(x, force_lsmas=True, cachedir=''), preset=[PresetBD, PresetAAC])
JP_NCOP = FileInfo(f"{config['bdmv_dir']}/かぐや様は告らせたい Vol.1/BD/BDMV/STREAM/00009.m2ts", (None, -24),
                   idx=lambda x: source(x, force_lsmas=True, cachedir=''))
JP_NCED = FileInfo(f"{config['bdmv_dir']}/かぐや様は告らせたい Vol.1/BD/BDMV/STREAM/00010.m2ts", (None, -24),
                   idx=lambda x: source(x, force_lsmas=True, cachedir=''))
JP_BD.name_file_final = VPath(fr"premux/{JP_BD.name} (Premux).mkv")
JP_BD.a_src_cut = VPath(JP_BD.name)


# OP/ED scenefiltering
opstart = 0
edstart = 32368
op_offset = 50
ed_offset = 1


zones: Dict[Tuple[int, int], Dict[str, Any]] = {  # Zones for the encoder
}


@initialise_input()
def filterchain(src: vs.VideoNode = JP_BD.clip_cut,
                ncop: vs.VideoNode = JP_NCOP.clip_cut,
                nced: vs.VideoNode = JP_NCED.clip_cut
                ) -> Union[vs.VideoNode, Tuple[vs.VideoNode, ...]]:
    """Main filterchain"""
    import debandshit as dbs
    import EoEfunc as eoe
    import havsfunc as haf
    import lvsfunc as lvf
    import rekt
    import vardefunc as vdf
    from awsmfunc import bbmod
    from vsutil import depth, get_w, get_y, insert_clip, iterate, scale_value

    assert src.format
    assert ncop.format
    assert nced.format

    src_c = src
    b = core.std.BlankClip(src, length=1)

    ncop = vdf.util.initialise_clip(ncop)
    nced = vdf.util.initialise_clip(nced)

    diff_rfs: List[Range] = []

    # OP/ED stack comps to check if they line up, as well as splicing them in
    return_scomp = []
    if opstart is not False:
        op_scomp = lvf.scomp(src[opstart:opstart+ncop.num_frames-1]+b, ncop[:-op_offset]+b)  # noqa
        diff_rfs += [(opstart, opstart+opstart+ncop.num_frames-1-op_offset)]
        src = insert_clip(src, ncop[:-op_offset], opstart)
        return_scomp += [op_scomp]
    if edstart is not False:
        ed_scomp = lvf.scomp(src[edstart:edstart+nced.num_frames-1]+b, nced[:-ed_offset]+b)  # noqa
        diff_rfs += [(edstart, edstart+opstart+nced.num_frames-1-ed_offset)]
        src = insert_clip(src, nced[:-ed_offset], edstart)
        return_scomp += [ed_scomp]

    return_scomp += [src]

    den_src, den_ncs = map(partial(core.dfttest.DFTTest, sigma=5), [src_c, src])
    den_src, den_ncs = depth(den_src, 32), depth(den_ncs, 32)
    diff = core.std.MakeDiff(den_src, den_ncs).dfttest.DFTTest(sigma=20.0)

    # For some reason there's noise from previous credits remaining? Removing that here
    diff_brz = vdf.misc.merge_chroma(depth(depth(diff.std.Binarize(0.025), 16).rgvs.RemoveGrain(3), 32), diff)
    diff = core.std.Expr([diff, diff_brz], "x y min")

    # And somehow it creates weird values in some places? Limiting here except for OP/ED
    diff_lim = diff.std.Limiter(0, 0)
    diff = lvf.rfs(diff_lim, diff, diff_rfs)

    return_scomp += [diff]
    # return return_scomp

    # Edgefixing (is it really dumb if it works? :cooldako: (don't answer that))
    rkt = rekt.rektlvls(src, [0, -1], [5, 5], [0, -1], [5, 5])
    fb = core.fb.FillBorders(rkt, left=1, right=1, top=1, bottom=1, mode="fillmargins")

    ef = fb.std.MaskedMerge(bbmod(src, top=1, bottom=1, left=2, right=2, y=True, u=False, v=False),
                            core.std.Expr([fb, rekt.rektlvls(fb, [0, -1], [-15, -15], [0, -1], [5, 5], [16, 256])],
                            f'x y - abs 0 > {scale_value(255, 8, 16)} 0 ?'), 0, True)
    bb_uv = depth(bbmod(ef, left=3, blur=20, y=False), 32)
    cshift = flt.chroma_shifter(bb_uv, src_left=0.25)

    src_y = get_y(cshift)

    # Descaling and rescaling
    l_mask = vdf.mask.FDOG().get_mask(src_y, lthr=0.125, hthr=0.027).rgsf.RemoveGrain(4).rgsf.RemoveGrain(4)
    l_mask = l_mask.std.Minimum().std.Deflate().std.Median().std.Convolution([1] * 9)
    sq_mask = lvf.mask.BoundingBox((4, 4), (src.width-4, src.height-4)).get_mask(src_y).std.Invert()

    descale = lvf.kernels.Catrom().descale(src_y, get_w(874), 874)
    upscale = lvf.kernels.Catrom().scale(descale, src.width, src.height)

    upscaled = vdf.scale.nnedi3cl_double(descale, use_znedi=True, pscrn=1)
    downscale = lvf.scale.ssim_downsample(upscaled, src.width, src.height)
    scaled = vdf.misc.merge_chroma(downscale, cshift)

    credit_mask = lvf.scale.descale_detail_mask(src_y, upscale, threshold=0.155)
    credit_mask = iterate(credit_mask, core.std.Inflate, 2)
    credit_mask = iterate(credit_mask, core.std.Maximum, 2)
    credit_mask = core.std.Expr([credit_mask, sq_mask], "x y -").std.Limiter()

    # Denoising and deblocking
    smd = depth(haf.SMDegrain(depth(scaled, 16), tr=3, thSAD=40), 32)
    ref = smd.dfttest.DFTTest(slocation=[0.0, 4, 0.25, 16, 0.3, 512, 1.0, 512], planes=[0], **eoe.freq._dfttest_args)
    bm3d = lvf.denoise.bm3d(smd, sigma=[0.2, 0], radius=3, ref=ref)

    # Detail mask for later
    ret = core.retinex.MSRCP(depth(get_y(smd), 16), sigma=[150, 300, 450], upper_thr=0.008)
    detail_mask = lvf.mask.detail_mask_neo(ret, sigma=6, lines_brz=0.02) \
        .rgvs.RemoveGrain(4).rgvs.RemoveGrain(4).std.Median().std.Convolution([1] * 9)

    # Chroma defuckery. This is pain.
    up_444 = vdf.scale.to_444(bm3d, bm3d.width, bm3d.height, join_planes=True)
    rgb_bm3d = lvf.kernels.Catrom().resample(up_444, format=vs.RGBS)
    corr_red = core.w2xnvk.Waifu2x(rgb_bm3d.std.Limiter(), noise=3, scale=1, model=2, precision=32)
    conv_yuv = lvf.kernels.BicubicDidee(chromaloc=0).resample(corr_red, bm3d.format.id, matrix=1)
    merge_chr = depth(core.std.Expr([bm3d, vdf.misc.merge_chroma(bm3d, conv_yuv)], "x y min"), 16)

    decs = vdf.noise.decsiz(merge_chr, sigmaS=8.0, min_in=200 << 8, max_in=240 << 8)

    # AA
    baa = lvf.aa.based_aa(decs, str(shader_file))
    sraa = lvf.sraa(decs, rfactor=1.35)
    clmp = lvf.aa.clamp_aa(decs, baa, sraa, strength=1.3)

    csharp = eoe.misc.ContraSharpening(clmp, decs, rep=13, planes=[1, 2])

    # Deband
    deband = [  # Why is the banding so damn STRONG holy shit
        dbs.debanders.dumb3kdb(csharp, radius=16, threshold=20, grain=[16, 12], seed=69420),
        dbs.debanders.dumb3kdb(csharp, radius=19, threshold=[28, 24], grain=[24, 12], seed=69420),
        flt.placebo_debander(csharp, radius=10, threshold=3.5, iterations=2, grain=4),
    ]
    deband = core.average.Mean(deband)
    deband = core.std.MaskedMerge(deband, csharp, detail_mask)

    # Some of my filtering seems to cause a tint? Fixing
    fix_tint = lvf.misc.shift_tint(deband, [0, 0, 0.28])

    # Merging credits and other 1080p detail
    restore_src = core.std.MaskedMerge(depth(fix_tint, 32), cshift, credit_mask)
    merge_creds = core.std.MergeDiff(restore_src, diff)

    return merge_creds


if __name__ == '__main__':
    FILTERED = filterchain()
    enc.Encoder(JP_BD, FILTERED).run(zones=zones)  # type: ignore
elif __name__ == '__vapoursynth__':
    FILTERED = filterchain()
    if not isinstance(FILTERED, vs.VideoNode):
        raise ImportError(f"Input clip has multiple output nodes ({len(FILTERED)})! Please output just 1 clip")
    else:
        enc.dither_down(FILTERED).set_output(0)
else:
    JP_BD.clip_cut.std.SetFrameProp('node', intval=0).set_output(0)
    FILTERED = filterchain()
    if not isinstance(FILTERED, vs.VideoNode):
        for i, clip_filtered in enumerate(FILTERED, start=1):
            clip_filtered.std.SetFrameProp('node', intval=i).set_output(i)
    else:
        FILTERED.std.SetFrameProp('node', intval=1).set_output(1)
