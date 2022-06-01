from typing import Any, Dict, List, Tuple

import vapoursynth as vs
import vsencode as vse
from lvsfunc.types import Range
from vardefunc import initialise_input

ini = vse.generate.init_project()

core = vse.util.get_vs_core(reserve_core=ini.reserve_core)

shader = vse.get_shader("FSRCNNX_x2_56-16-4-1.glsl")

# Sources
SRC = vse.FileInfo(f"{ini.bdmv_dir}/[BDMV]HONZUKI/HONZUKI_2/BDMV/STREAM/00011.m2ts", (24, -24))
US_NCOP = vse.FileInfo(f"{ini.bdmv_dir} (US)/Ascendance of a Bookworm BD-3/BDMV/STREAM/00053.m2ts", (24, -24))

# OP/ED scenefiltering
opstart = 0
op_offset = 2


str_deband_ranges: List[Range] = [  # Ranges with stronger banding
]


zones: Dict[Tuple[int, int], Dict[str, Any]] = {  # Zones for the encoder
}


if opstart is not False:
    str_deband_ranges += [(opstart+247, opstart+368)]
    op_replace_chr: List[Range] = [(827, 846)]


@initialise_input(bits=32)
def filterchain(src: vs.VideoNode = SRC.clip_cut) -> vs.VideoNode | Tuple[vs.VideoNode, ...]:
    """Main filterchain. Special thanks to Samaritan for sharing his script."""
    import adptvgrnMod as adp
    import debandshit as dbs
    import havsfunc as haf
    import lvsfunc as lvf
    import vardefunc as vdf
    import vsdenoise as vsd
    import vsmask as vsm
    from vsutil import depth, get_w, get_y, iterate
    from xvs import mwcfix

    assert src.format

    us_ncop = vdf.initialise_clip(US_NCOP.clip_cut, bits=32)
    us_ncop_cmerge = vdf.merge_chroma(src, us_ncop)
    src = lvf.rfs(src, us_ncop_cmerge, op_replace_chr)

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
        planes.Y = core.std.MaskedMerge(merge_lineart, src_y, credit_mask)

    scaled = depth(planes.clip, 16)

    # Denoising, AA, weak chroma fix
    smd = haf.SMDegrain(get_y(scaled), tr=2, thSAD=150)
    bm3d = vsd.BM3DCudaRTC(scaled, [0.5, 0], radius=3, ref=smd).clip
    knlm = vsd.knl_means_cl(bm3d, strength=0.35, channels=vsd.ChannelMode.CHROMA)
    decs = vdf.noise.decsiz(knlm, min_in=200 << 8, max_in=240 << 8)

    aa = lvf.aa.nneedi3_clamp(decs, strength=1.4, mask=depth(l_mask, 16).std.Limiter())

    cfix = mwcfix(aa, warp=3)

    # Debanding and graining
    detail_mask = lvf.mask.detail_mask_neo(cfix)
    deband = dbs.dumb3kdb(cfix, radius=18, threshold=[32, 24, 24], grain=12)
    deband = core.std.MaskedMerge(deband, cfix, detail_mask)

    deband_str = dbs.dumb3kdb(cfix, radius=24, threshold=[64, 48, 48], grain=[24, 12])
    deband_str = core.std.MaskedMerge(deband_str, cfix, detail_mask)

    deband = lvf.rfs(deband, deband_str, str_deband_ranges)

    grain = adp.adptvgrnMod(deband, strength=0.25, size=1.15, luma_scaling=8)

    return grain


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
