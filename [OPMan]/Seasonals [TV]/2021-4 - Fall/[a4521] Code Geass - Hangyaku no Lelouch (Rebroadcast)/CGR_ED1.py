from typing import Any, Dict, List, Tuple, Union

import vapoursynth as vs
from lvsfunc.misc import source
from lvsfunc.types import Range
from vardautomation import FileInfo, PresetWEB, PresetAAC, VPath

from project_module import encoder as enc

core = vs.core


# Sources
JP_TV = FileInfo(r'src/Code Geass - Hangyaku no Lelouch - 01 [15th Anniversary Rebroadcast] (TBS).d2v', (50972, 53670),
                 preset=[PresetWEB, PresetAAC], idx=lambda x: source(x))
JP_TV.name_file_final = VPath(fr"premux/{JP_TV.name} (Premux).mkv")
JP_TV.a_src = VPath(JP_TV.path.to_str()[:-4] + ".aac")
JP_TV.a_src_cut = VPath(JP_TV.path.to_str()[:-4] + "_cut.aac")
JP_TV.do_qpfile = True


zones: Dict[Tuple[int, int], Dict[str, Any]] = {  # Zones for x265
}


def filterchain() -> Union[vs.VideoNode, Tuple[vs.VideoNode, ...]]:
    """Main filterchain"""
    import debandshit as dbs
    import lvsfunc as lvf
    from adptvgrnMod import adptvgrnMod
    from vsutil import depth

    src = JP_TV.clip_cut
    vfm = core.vivtc.VFM(src, order=1)
    vdec = core.vivtc.VDecimate(vfm)
    src = depth(vdec, 16)

    stretch = lvf.kernels.Catrom().scale(src, 1920, 1080)
    debl = lvf.deblock.autodb_dpir(stretch, strs=[15, 20, 35], matrix=1, cuda=True)
    deband = dbs.dumb3kdb(debl, radius=18, threshold=[24, 16])
    grain: vs.VideoNode = adptvgrnMod(deband, strength=0.3, size=1.3, sharp=80, grain_chroma=False,
                                      static=False, seed=42069, luma_scaling=8)

    return grain


if __name__ == '__main__':
    enc.Encoder(JP_TV, filterchain()).run(clean_up=True)  # type: ignore
elif __name__ == '__vapoursynth__':
    FILTERED = filterchain()
    if not isinstance(FILTERED, vs.VideoNode):
        raise ImportError(f"Input clip has multiple output nodes ({len(FILTERED)})! Please output a single clip")
    else:
        enc.dither_down(FILTERED).set_output(0)
else:
    JP_TV.clip_cut.std.SetFrameProp('node', intval=0).set_output(0)
    FILTERED = filterchain()
    if not isinstance(FILTERED, vs.VideoNode):
        for i, clip_filtered in enumerate(FILTERED, start=1):
            clip_filtered.std.SetFrameProp('node', intval=i).set_output(i)
    else:
        FILTERED.std.SetFrameProp('node', intval=1).set_output(1)
