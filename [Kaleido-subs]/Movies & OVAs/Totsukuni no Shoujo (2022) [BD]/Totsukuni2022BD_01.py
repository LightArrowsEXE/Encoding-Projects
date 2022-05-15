from __future__ import annotations

import multiprocessing as mp
import os
from pathlib import Path
from typing import Any, Dict, Tuple

import vapoursynth as vs
import yaml
from lvsfunc.misc import source
from vardautomation import FileInfo, PresetBD, VPath, get_vs_core
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
JP_BD = FileInfo(f"{config['bdmv_dir']}/The Girl from the Other Side.mkv", (24, -24),
                 idx=lambda x: source(x, cachedir='', force_lsmas=True), preset=[PresetBD])
JP_BD.name_file_final = enc.parse_name(config, __file__)
JP_BD.a_src_cut = VPath(JP_BD.name)


zones: Dict[Tuple[int, int], Dict[str, Any]] = {  # Zones for the encoder
}


@initialise_input()
def filterchain(src: vs.VideoNode = JP_BD.clip_cut) -> vs.VideoNode | Tuple[vs.VideoNode, ...]:
    """Main filterchain"""
    import havsfunc as haf
    import vardefunc as vdf
    from ccd import ccd
    from vsmask.edge import FDOG
    from vsutil import get_y, insert_clip

    assert src.format

    smd = haf.SMDegrain(src, tr=3, thSAD=110, blksize=16)

    ret_smd = core.retinex.MSRCP(get_y(smd), sigma=[50, 200, 350], upper_thr=0.005)
    l_mask = FDOG().get_mask(ret_smd, lthr=102 << 8, hthr=102 << 8).std.Maximum().std.Minimum().std.Minimum()
    l_mask = l_mask.std.Minimum().std.Median().std.Convolution([1] * 9)  # stolen from varde xd

    ccd_uv = ccd(smd, threshold=12)
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


if __name__ == '__main__':
    enc.Encoder(JP_BD, filterchain()).run(zones=zones, x264=True, resumable=False, all_tracks=True)
elif __name__ == '__vapoursynth__':
    FILTERED = filterchain()
    if not isinstance(FILTERED, vs.VideoNode):
        raise ImportError(f"Input clip has multiple output nodes ({len(FILTERED)})! Please output a single clip")
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
