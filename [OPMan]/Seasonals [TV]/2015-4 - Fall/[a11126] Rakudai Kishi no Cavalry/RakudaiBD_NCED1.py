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
from vsutil import insert_clip

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
JP_BD = FileInfo(f"{config['bdmv_dir']}/RAKUDAI_KISHI_NO_CAVALRY_VOL2/BDROM/BDMV/STREAM/00002.m2ts", (24, -24),
                 idx=lambda x: source(x), preset=[PresetBD])
JP_BD.name_file_final = enc.parse_name(config, __file__)
JP_BD.a_src_cut = VPath(JP_BD.name)


zones: Dict[Tuple[int, int], Dict[str, Any]] = {  # Zones for the encoder
}


@initialise_input(bits=32)
def filterchain(src: vs.VideoNode = JP_BD.clip_cut) -> vs.VideoNode | Tuple[vs.VideoNode, ...]:
    """Main filterchain"""
    import havsfunc as haf
    import kagefunc as kgf
    import lvsfunc as lvf
    import vardefunc as vdf
    from ccd import ccd
    from vsutil import depth, get_w, get_y

    assert src.format

    src_y = get_y(src)

    l_mask = vdf.mask.FDOG().get_mask(src_y, lthr=0.175, hthr=0.175).rgsf.RemoveGrain(4).rgsf.RemoveGrain(4)
    l_mask = l_mask.std.Minimum().std.Deflate().std.Median().std.Convolution([1] * 9)

    descale = lvf.kernels.Bicubic(b=.2, c=.4).descale(src_y, get_w(720), 720)
    upscale = vdf.scale.fsrcnnx_upscale(descale, 1920, 1080, shader_file,
                                        downscaler=lvf.scale.ssim_downsample,
                                        undershoot=1.1, overshoot=1.5)
    upscale_min = core.akarin.Expr([src_y, upscale], "x y min")
    rescale = core.std.MaskedMerge(src_y, upscale_min, l_mask)
    scaled = depth(vdf.misc.merge_chroma(rescale, src), 16)

    smd = haf.SMDegrain(scaled, tr=3, thSAD=50)
    ccd_uv = ccd(smd, threshold=3)
    decs = vdf.noise.decsiz(ccd_uv, min_in=192 << 8, max_in=240 << 8)

    deband = flt.masked_f3kdb(decs, rad=18, thr=[24, 12], grain=[24, 12])

    deb_trim = deband[1985:-1]
    crossfade = kgf.crossfade(deb_trim, deband[-1] * deb_trim.num_frames, deb_trim.num_frames - 1)
    crossfade = insert_clip(deband, crossfade, 1985)

    return crossfade


if __name__ == '__main__':
    enc.Encoder(JP_BD, filterchain()).run(zones=zones, flac=True)
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
