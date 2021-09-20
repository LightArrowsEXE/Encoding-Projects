from typing import Any, Dict, Tuple

import vapoursynth as vs
from lvsfunc.misc import source
from vardautomation import FileInfo, PresetAAC, PresetBD, VPath

from project_module import chain, encode

core = vs.core


# Sources
JP_BD = FileInfo(r'BDMV/GRANBLUE_FANTASY_SEASON2_4/BDMV/STREAM/00002.m2ts', (None, -25),
                 idx=lambda x: source(x, force_lsmas=True, cachedir=''),
                 preset=[PresetBD, PresetAAC])
JP_BD.name_file_final = VPath(fr"premux/{JP_BD.name} (Premux).mkv")
JP_BD.a_src_cut = VPath(f"{JP_BD.name}_cut.aac")
JP_BD.do_qpfile = True

zones: Dict[Tuple[int, int], Dict[str, Any]] = {  # Zones for x265
    (25308, 26738): {'b': 0.75},
    (26808, 27089): {'b': 0.75},
    (27234, 27864): {'b': 0.75},
}

if __name__ == '__main__':
    filtered = chain.filterchain(JP_BD.clip_cut)
    encode.Encoder(JP_BD, filtered).run(zones=zones)
elif __name__ == '__vapoursynth__':
    filtered = chain.filterchain(JP_BD.clip_cut)
    if not isinstance(filtered, vs.VideoNode):
        raise RuntimeError("Multiple output nodes were set when `vspipe` only expected one")
    else:
        filtered.set_output(0)
else:
    JP_BD.clip_cut.set_output(0)
    FILTERED = chain.filterchain(JP_BD.clip_cut)
    if not isinstance(FILTERED, vs.VideoNode):
        for i, clip_filtered in enumerate(FILTERED, start=1):  # type: ignore
            clip_filtered.set_output(i)
    else:
        FILTERED.set_output(1)
