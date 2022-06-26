from __future__ import annotations

from typing import Any, Dict, Tuple

import vapoursynth as vs
import vsencode as vse
from vardefunc import initialise_input

from project_module import flt

ini = vse.generate.init_project()

core = vse.util.get_vs_core(reserve_core=ini.reserve_core)

shader = vse.get_shader("FSRCNNX_x2_56-16-4-1.glsl")


# Sources
SRC = vse.FileInfo(f"{ini.bdmv_dir}/The Girl from the Other Side.mkv", (24, -24))


zones: Dict[Tuple[int, int], Dict[str, Any]] = {  # Zones for the encoder
}


@initialise_input()
def filterchain(src: vs.VideoNode = SRC.clip_cut) -> vs.VideoNode | Tuple[vs.VideoNode, ...]:
    """Main filterchain"""
    import havsfunc as haf
    import jvsfunc as jvf
    import vardefunc as vdf
    from vsmask.edge import FDOG
    from vsutil import get_y, insert_clip

    assert src.format

    smd = haf.SMDegrain(src, tr=3, thSAD=110, blksize=16)

    ret_smd = core.retinex.MSRCP(get_y(smd), sigma=[50, 200, 350], upper_thr=0.005)
    l_mask = FDOG().get_mask(ret_smd, lthr=102 << 8, hthr=102 << 8).std.Maximum().std.Minimum().std.Minimum()
    l_mask = l_mask.std.Minimum().std.Median().std.Convolution([1] * 9)  # stolen from varde xd

    ccd_uv = jvf.ccd(smd, threshold=12)
    ccd_uv = core.std.MaskedMerge(ccd_uv, smd, l_mask)

    # Slight cleaning fun stuff
    credit = core.std.Binarize(get_y(src[100506])).std.Convolution([1] * 9)
    dft = core.dfttest.DFTTest(src, sigma=50)

    final_credit = ccd_uv[100465:]
    final_credit = core.std.MaskedMerge(final_credit, dft[100465:], credit)
    final_credit = insert_clip(ccd_uv, final_credit, 100465)

    deband = flt.masked_f3kdb(final_credit, rad=16, thr=[12, 6], grain=[32, 0])

    decs = vdf.noise.decsiz(deband, min_in=208 << 8, max_in=240 << 8)

    return decs


FILTERED = filterchain()


if __name__ == '__main__':
    vse.EncodeRunner(SRC, FILTERED).video('x264', '.settings/x264_settings', zones=zones) \
        .audio('aac', all_tracks=True).mux('LightArrowsEXE@Kaleido').run()
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
        audio_node.set_output(i)
