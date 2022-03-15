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
    hookpath = r"mpv/shaders/FSRCNNX_x2_16-0-4-1.glsl"
    shader_file = os.path.join(str(os.getenv("APPDATA")), hookpath)


# Sources
SRC = FileInfo(f"{config['bdmv_dir']}/[BDMV][150408][Absolute Duo][Vol.01]/ABSOLUTE_DUO_VOL1/BDMV/STREAM/00005.m2ts",
               (24, -24), idx=lambda x: source(x, force_lsmas=True, cachedir=''), preset=[PresetBD])
SRC.name_file_final = enc.parse_name(config, __file__)
SRC.a_src_cut = VPath(SRC.name)


zones: Dict[Tuple[int, int], Dict[str, Any]] = {  # Zones for the encoder
}


@initialise_input(bits=32)
def filterchain(src: vs.VideoNode = SRC.clip_cut) -> vs.VideoNode | Tuple[vs.VideoNode, ...]:
    """Main filterchain"""
    import havsfunc as haf
    import kagefunc as kgf
    import lvsfunc as lvf
    import vardefunc as vdf
    import vsdenoise as vsd
    from ccd import ccd
    from vsutil import depth

    assert src.format

    descale = lvf.scale.comparative_descale(src, kernel=lvf.kernels.Spline16())
    upscale = vdf.scale.fsrcnnx_upscale(descale, shader_file=shader_file, strength=85,
                                        downscaler=lvf.scale.ssim_downsample,
                                        undershoot=1.1, overshoot=1.5)
    scaled = depth(vdf.misc.merge_chroma(upscale, src), 16)

    smd = haf.SMDegrain(scaled, tr=3, thSAD=25)
    bm3d = vsd.BM3DCudaRTC(smd, sigma=[0.90, 0], refine=3).clip
    cc = ccd(bm3d, threshold=6)
    decs = vdf.noise.decsiz(cc, min_in=196 << 8, max_in=240 << 8)

    aa = lvf.aa.based_aa(decs, shader_file, rfactor=1.25, beta=0.6)

    deband = flt.masked_f3kdb(aa, rad=24, thr=[32, 24], grain=[24, 12])
    str_deband = core.average.Mean([deband, flt.masked_placebo(aa, rad=24, thr=7.5, grain=8)])
    deband = lvf.rfs(deband, str_deband, [(None, 52), (1356, 1396)])

    grain = kgf.adaptive_grain(deband, 0.1, luma_scaling=10)

    t = lvf.src(r"premux/ADBD_NCOP1 (Premux).mkv")
    t2 = lvf.src(r"premux/ADBD_NCOP1 (Premux)_old.mkv")

    return grain, t2, t


if __name__ == '__main__':
    enc.Encoder(SRC, filterchain()).run(zones=zones, flac=True)
elif __name__ == '__vapoursynth__':
    FILTERED = filterchain()
    if not isinstance(FILTERED, vs.VideoNode):
        raise ImportError(f"Input clip has multiple output nodes ({len(FILTERED)})! Please output a single clip")
    else:
        enc.dither_down(FILTERED).set_output(0)
else:
    SRC.clip_cut.std.SetFrameProp('node', intval=0).set_output(0)
    FILTERED = filterchain()

    if not isinstance(FILTERED, vs.VideoNode):
        for i, clip_filtered in enumerate(FILTERED, start=1):
            clip_filtered.std.SetFrameProp('node', intval=i).set_output(i)
    else:
        FILTERED.std.SetFrameProp('node', intval=1).set_output(1)
