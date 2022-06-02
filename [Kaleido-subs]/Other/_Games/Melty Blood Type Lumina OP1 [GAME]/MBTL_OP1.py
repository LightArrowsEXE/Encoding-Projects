import os
from pathlib import Path
from typing import Tuple, Union

import vapoursynth as vs
from lvsfunc.misc import source
from vardautomation import FileInfo, PresetBD, PresetFLAC, VPath

from project_module import encoder as enc
from project_module import flt

core = vs.core


shader_file = Path(r'assets/FSRCNNX_x2_56-16-4-1.glsl')
if not shader_file.exists:
    hookpath = r"mpv/shaders/FSRCNNX_x2_56-16-4-1.glsl"
    shader_file = os.path.join(os.getenv("APPDATA"), hookpath)


# Sources
JP_BD = FileInfo(r'src/4mx21x.mkv', (None, None), preset=[PresetBD, PresetFLAC],
                 idx=lambda x: source(x, force_lsmas=True, cachedir=''))
JP_BD.name_file_final = VPath(fr"premux/{JP_BD.name} (Premux).mkv")
JP_BD.a_src_cut = VPath("stack black.flac")
JP_BD.do_qpfile = True


"""
    Switch OP has significantly more detail, but the Steam OP has much less haloing
    and weird "wavey" artefacting (but also uses the wrong colourspace lol).

    I can't really take the best of both worlds unfortunately,
    so it's a trade-off between whether you like having more detail or less artefacting.
    If you prefer less artefacting, grab the OPMan release. Else this one.
"""


def filterchain() -> Union[vs.VideoNode, Tuple[vs.VideoNode, ...]]:
    """Main filterchain"""
    import lvsfunc as lvf
    import vardefunc as vdf
    from vsutil import depth, split, join
    from finedehalo import fine_dehalo

    src = JP_BD.clip_cut
    src = depth(src, 16)
    src = core.resize.Bicubic(src, chromaloc_in=1, chromaloc=0)

    debl = lvf.deblock.vsdpir(src, strength=1, i444=True)
    debl = depth(debl, 16)
    decs = vdf.noise.decsiz(debl, sigmaS=8, min_in=200 << 8, max_in=235 << 8)

    planes = split(decs)
    planes[2] = fine_dehalo(planes[2], rx=2, ry=2, brightstr=0.9, darkstr=0)
    cdehalo = join(planes)

    dehalo = lvf.dehalo.bidehalo(cdehalo, sigmaS=1.5, sigmaS_final=1)

    baa = lvf.aa.based_aa(dehalo, str(shader_file))
    sraa = lvf.sraa(dehalo, rfactor=1.65)
    clmp = lvf.aa.clamp_aa(dehalo, baa, sraa, strength=1.3)

    deband = flt.masked_f3kdb(clmp, thr=[32, 24])

    grain = vdf.noise.Graigasm(  # Mostly stolen from Varde tbh
        thrs=[x << 8 for x in (32, 80, 128, 176)],
        strengths=[(0.25, 0.0), (0.2, 0.0), (0.15, 0.0), (0.0, 0.0)],
        sizes=(1.15, 1.1, 1.05, 1),
        sharps=(65, 50, 40, 40),
        grainers=[
            vdf.noise.AddGrain(seed=69420, constant=True),
            vdf.noise.AddGrain(seed=69420, constant=False),
            vdf.noise.AddGrain(seed=69420, constant=False)
        ]).graining(deband)

    return grain


if __name__ == '__main__':
    enc.Encoder(JP_BD, filterchain()).run(clean_up=False)  # type: ignore
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
