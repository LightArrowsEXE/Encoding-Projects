from typing import Any, Dict, List, Tuple

import vapoursynth as vs
import vsencode as vse
from lvsfunc.types import Range
from vardefunc import initialise_input

ini = vse.generate.init_project()

core = vse.util.get_vs_core(reserve_core=ini.reserve_core)

shader = vse.get_shader("FSRCNNX_x2_56-16-4-1.glsl")

# Sources
SRC = vse.FileInfo(f"{ini.bdmv_dir}/[BDMV]HONZUKI/HONZUKI_2/BDMV/STREAM/00013.m2ts", (24, -24))

# OP/ED scenefiltering
edstart = 0
ed_offset = 1


no_rescale: List[Range] = [  # Ranges that should not be getting descaled
]


zones: Dict[Tuple[int, int], Dict[str, Any]] = {  # Zones for the encoder
}


if edstart is not False:
    no_rescale += [(edstart, edstart+SRC.clip_cut.num_frames-1-ed_offset)]


@initialise_input()
def filterchain(src: vs.VideoNode = SRC.clip_cut) -> vs.VideoNode | Tuple[vs.VideoNode, ...]:
    """Main filterchain. Special thanks to Samaritan for sharing his script."""
    import adptvgrnMod as adp
    import debandshit as dbs
    import havsfunc as haf
    import jvsfunc as jvf
    import lvsfunc as lvf
    import vardefunc as vdf
    import vsdenoise as vsd
    import vsmask as vsm
    from vsutil import depth, get_y
    from xvs import mwcfix

    assert src.format

    src_y = get_y(src)
    l_mask = vsm.edge.FDOG().get_mask(src_y, lthr=0.125, hthr=0.025).rgsf.RemoveGrain(4).rgsf.RemoveGrain(4)
    l_mask = l_mask.std.Minimum().std.Deflate().std.Median().std.Convolution([1] * 9)

    # Denoising, AA, weak chroma fix
    smd = haf.SMDegrain(get_y(scaled), tr=2, thSAD=150)
    bm3d = vsd.BM3DCudaRTC(scaled, [0.5, 0], radius=3, ref=smd).clip
    knlm = vsd.knl_means_cl(bm3d, strength=0.35, channels=vsd.ChannelMode.CHROMA)
    decs = vdf.noise.decsiz(knlm, min_in=200 << 8, max_in=240 << 8)

    aa = lvf.aa.nneedi3_clamp(decs, strength=1.4, mask=depth(l_mask, 16).std.Limiter())
    aa = lvf.rfs(aa, decs, no_rescale[-1])  # Do not AA the ED

    cfix = mwcfix(aa, warp=3)

    # Debanding and graining
    detail_mask = lvf.mask.detail_mask_neo(cfix)
    deband = dbs.dumb3kdb(cfix, radius=18, threshold=[32, 24, 24], grain=12)
    deband = core.std.MaskedMerge(deband, cfix, detail_mask)

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
