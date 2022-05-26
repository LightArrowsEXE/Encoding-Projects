from typing import Any, Dict, List, Tuple

import vapoursynth as vs
import vsencode as vse
from lvsfunc.misc import source
from lvsfunc.types import Range
from vardefunc import initialise_input

ini = vse.generate.init_project()

core = vse.util.get_vs_core(reserve_core=ini.reserve_core)

shader = vse.get_shader("FSRCNNX_x2_56-16-4-1.glsl")

# Sources
SRC = vse.FileInfo(f"{ini.bdmv_dir}/[BDMV]HONZUKI/HONZUKI_3/BDMV/STREAM/00004.m2ts", (24, -24))
NCOP = vse.FileInfo(f"{ini.bdmv_dir}/[BDMV]HONZUKI/HONZUKI_4/BDMV/STREAM/00011.m2ts", (24, -24))
NCED = vse.FileInfo(f"{ini.bdmv_dir}/[BDMV]HONZUKI/HONZUKI_4/BDMV/STREAM/00013.m2ts", (24, -24))

dark_house_mask: vs.VideoNode = source(".assets/common/dark_house.png", ref=SRC.clip_cut)  # Thanks Moelancholy!


# OP/ED scenefiltering
opstart = 432
edstart = 31264
op_offset = 2
ed_offset = 5


mask_dark_house: List[Range] = [  # Masked deband of a commonly occuring shot of Myne's house
]

no_rescale: List[Range] = [  # Ranges that should not be getting descaled
    (SRC.clip_cut.num_frames-120, SRC.clip_cut.num_frames-1)
]

replace_chroma: List[Range] = [  # Replacing chroma with the US chroma
]

str_deband_ranges: List[Range] = [  # Ranges with stronger banding
]


zones: Dict[Tuple[int, int], Dict[str, Any]] = {  # Zones for the encoder
}


if edstart is not False:
    no_rescale += [(edstart, edstart+NCED.clip_cut.num_frames-1-ed_offset)]


@initialise_input()
def filterchain(src: vs.VideoNode = SRC.clip_cut,
                ncop: vs.VideoNode = NCOP.clip_cut,
                nced: vs.VideoNode = NCED.clip_cut
                ) -> vs.VideoNode | Tuple[vs.VideoNode, ...]:
    """Main filterchain. Special thanks to Samaritan for sharing his script."""
    from functools import partial

    import debandshit as dbs
    import havsfunc as haf
    import jvsfunc as jvf
    import lvsfunc as lvf
    import vardefunc as vdf
    import vsdenoise as vsd
    import vsmask as vsm
    from vsutil import depth, get_w, insert_clip, iterate
    from xvs import mwcfix

    assert src.format
    assert ncop.format
    assert nced.format

    src_c: vs.VideoNode = src
    b = core.std.BlankClip(src, length=1)

    ncop = vdf.util.initialise_clip(ncop)
    nced = vdf.util.initialise_clip(nced)

    # Extend to make sure I catch any final frames
    nced = nced + nced[-1] * 2

    diff_rfs: List[Range] = []

    # OP/ED stack comps to check if they line up, as well as splicing them in
    return_scomp = []
    if opstart is not False:
        op_scomp = lvf.scomp(src[opstart:opstart+ncop.num_frames-1]+b, ncop[:-op_offset]+b)  # noqa
        diff_rfs += [(opstart, opstart+ncop.num_frames-1-op_offset)]
        src = insert_clip(src, ncop[:-op_offset], opstart)
        return_scomp += [op_scomp]
    if edstart is not False:
        ed_scomp = lvf.scomp(src[edstart:edstart+nced.num_frames-1]+b, nced[:-ed_offset]+b)  # noqa
        diff_rfs += [(edstart, edstart+nced.num_frames-1-ed_offset)]
        src = insert_clip(src, nced[:-ed_offset], edstart)
        return_scomp += [ed_scomp]

    return_scomp += [src]

    den_src, den_ncs = map(partial(core.dfttest.DFTTest, sigma=5), [src_c, src])
    den_src, den_ncs = depth(den_src, 32), depth(den_ncs, 32)
    diff = core.std.MakeDiff(den_src, den_ncs).dfttest.DFTTest(sigma=20.0)

    # For some reason there's ugly noise around the credits? Removing that here.
    diff_brz = vdf.misc.merge_chroma(depth(depth(diff.std.Binarize(0.025), 16), 32), diff)
    diff = core.std.Expr([diff, diff_brz.std.Inflate().std.Maximum()], "x y min")

    # And somehow it creates weird values in some places? Limiting here except for OP/ED
    diff_lim = core.std.BlankClip(diff)
    diff = lvf.rfs(diff_lim, diff, diff_rfs)

    return_scomp += [diff]
    # return return_scomp

    src = depth(src, 32)

    # Rescaling
    with vdf.YUVPlanes(src) as planes:
        src_y = planes.Y

        l_mask = vsm.edge.FDOG().get_mask(src_y, lthr=0.125, hthr=0.025).rgsf.RemoveGrain(4).rgsf.RemoveGrain(4)
        l_mask = l_mask.std.Minimum().std.Deflate().std.Median().std.Convolution([1] * 9)
        sq_mask = lvf.mask.BoundingBox((4, 4), (src.width-4, src.height-4)).get_mask(src_y).std.Invert()

        descale = lvf.kernels.Catrom().descale(src_y, get_w(812), 812)
        upscale = lvf.kernels.Catrom().scale(descale, src.width, src.height)

        credit_mask = lvf.scale.descale_detail_mask(src_y, upscale, threshold=0.035)
        credit_mask = iterate(credit_mask, core.std.Inflate, 2)
        credit_mask = iterate(credit_mask, core.std.Maximum, 2)
        credit_mask = core.std.Expr([credit_mask, sq_mask], "x y -").std.Limiter()

        rescale = vdf.scale.fsrcnnx_upscale(descale, src.width, src.height, shader,
                                            downscaler=lvf.scale.ssim_downsample,
                                            overshoot=1.1, undershoot=1.5,
                                            profile='slow', strength=40)
        merge_lineart = core.std.MaskedMerge(src_y, depth(rescale, 32), l_mask)
        merge_credits = core.std.MaskedMerge(merge_lineart, src_y, credit_mask)
        planes.Y = lvf.rfs(merge_credits, src_y, no_rescale)

    scaled = depth(planes.clip, 16)

    # Denoising, AA, weak chroma fix
    smd = haf.SMDegrain(scaled, tr=3, thSAD=50, Str=1.25)
    knlm = vsd.knl_means_cl(smd, strength=0.35, tr=1, sr=2)
    ccd = jvf.ccd(knlm, threshold=3, mode=3)
    decs = vdf.noise.decsiz(ccd, min_in=200 << 8, max_in=240 << 8)

    aa = lvf.aa.nneedi3_clamp(decs, strength=1.4, mask=depth(l_mask, 16).std.Limiter())
    aa = lvf.rfs(aa, decs, no_rescale[-1])  # Do not AA the ED

    cfix = mwcfix(aa, warp=3)

    # Debanding and graining
    detail_mask = lvf.mask.detail_mask_neo(cfix)
    deband = dbs.dumb3kdb(cfix, radius=18, threshold=[32, 24, 24], grain=12)
    deband = core.std.MaskedMerge(deband, cfix, detail_mask)

    deband_str = dbs.dumb3kdb(cfix, radius=24, threshold=[64, 48, 48], grain=[24, 12])
    deband_str = core.std.MaskedMerge(deband_str, cfix, detail_mask)

    deband = lvf.rfs(deband, deband_str, str_deband_ranges)

    if mask_dark_house:
        deband_dark = core.placebo.Deband(aa, radius=18, threshold=6.5, grain=4, iterations=2, planes=7)
        deband_dark = deband_dark.noise.Add(var=0.30, type=2)
        deband_dark = core.std.MaskedMerge(deband, deband_dark, depth(dark_house_mask, 16))
        deband = lvf.rfs(deband, deband_dark, mask_dark_house)

    adap_mask = core.adg.Mask(deband.std.PlaneStats(), 8)
    grain = deband.noise.Add(var=0.20, type=2)
    grain = core.std.MaskedMerge(deband, grain, adap_mask)

    # Merging credits and other 1080p detail
    restore_src = core.std.MaskedMerge(depth(grain, 32), src, credit_mask)
    diff_creds = core.std.MergeDiff(restore_src, diff)

    # Minor speed-up right at the end by freezeframing the endcard. There's never animation anyway
    freeze = core.std.FreezeFrames(
        diff_creds, [src.num_frames-120], [src.num_frames-1], [src.num_frames-120]
    )

    return freeze


FILTERED = filterchain()


if __name__ == '__main__':
    vse.EncodeRunner(SRC, FILTERED).video('x265', '.settings/x265_settings', zones=zones) \
        .audio('aac').mux('LightArrowsEXE@GoodJobMedia').run()
elif __name__ == '__vapoursynth__':
    if not isinstance(FILTERED, vs.VideoNode):
        raise vs.Error(f"Input clip has multiple output nodes ({len(FILTERED)})! Please output a single clip")
    else:
        vse.video.finalize_clip(FILTERED).set_output(0)
else:
    SRC.clip_cut.set_output(0)

    if not isinstance(FILTERED, vs.VideoNode):
        for i, clip_filtered in enumerate(FILTERED, start=1):
            clip_filtered.set_output(i)
    else:
        FILTERED.set_output(1)

    for i, audio_node in enumerate(SRC.audios_cut, start=10):
        if audio_node.bits_per_sample == 32:
            audio_node.set_output(i)
