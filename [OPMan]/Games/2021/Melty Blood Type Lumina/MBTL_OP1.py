import os
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union

import vapoursynth as vs
from lvsfunc.misc import source
from lvsfunc.types import Range
from vardautomation import FileInfo, PresetBD, PresetFLAC, VPath

from project_module import encoder as enc

core = vs.core


shader_file = 'assets/FSRCNNX_x2_56-16-4-1.glsl'
if not Path(shader_file).exists():
    hookpath = r"mpv/shaders/FSRCNNX_x2_56-16-4-1.glsl"
    shader_file = os.path.join(str(os.getenv("APPDATA")), hookpath)


# Sources
JP_BD = FileInfo(r'src/MB_OP.wmv', (None, None), preset=[PresetBD, PresetFLAC],
                 idx=lambda x: source(x, force_lsmas=True, cachedir=''))
JP_BD.name_file_final = VPath(fr"premux/{JP_BD.name} (Premux).mkv")
JP_BD.a_src_cut = VPath(JP_BD.name)
JP_BD.do_qpfile = True


# OP filtering
opstart = 0

aliasing_ranges: List[Range] = [  # Ranges with aliasing
    (opstart+144, opstart+349), (opstart+1940, opstart+1959), (opstart+2119, opstart+2126)
]

haloing_ranges: List[Range] = [  # Ranges with haloing
    (opstart+1876, 1886)
]

zones: Dict[Tuple[int, int], Dict[str, Any]] = {  # Zones for x265
}


def filterchain() -> Union[vs.VideoNode, Tuple[vs.VideoNode, ...]]:
    """Main filterchain"""
    import debandshit as dbs
    import havsfunc as haf
    import lvsfunc as lvf
    import vardefunc as vdf
    from adptvgrnMod import adptvgrnMod
    from vsutil import depth

    src = JP_BD.clip_cut
    src = depth(src, 16)
    up = vdf.scale.to_444(src, src.width, src.height, join_planes=True)

    cbl = haf.FixChromaBleedingMod(up, cx=-0.35, cy=0, thr=4, strength=1, blur=False)
    debl = lvf.deblock.vsdpir(cbl, matrix=1, strength=25, mode='deblock', i444=True)

    aa = lvf.aa.nneedi3_clamp(debl, strength=1.5)
    aa = lvf.rfs(debl, aa, aliasing_ranges)
    aa = depth(aa, 16).std.Limiter(16 >> 8, [235 << 8, 240 << 8], [0, 1, 2])

    dehalo = lvf.dehalo.masked_dha(aa, brightstr=0.35)
    dehalo = lvf.rfs(aa, dehalo, haloing_ranges)

    deband = dbs.dumb3kdb(dehalo, threshold=[16, 12])
    grain: vs.VideoNode = adptvgrnMod(deband, strength=0.15, size=1.15, sharp=70, grain_chroma=False,
                                      static=False, seed=42069, luma_scaling=10)

    return grain


if __name__ == '__main__':
    enc.Encoder(JP_BD, filterchain()).run(clean_up=True)  # type: ignore
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
