import os
from pathlib import Path
from typing import Any, Dict, Tuple, Union

import vapoursynth as vs
from lvsfunc.misc import source
from vardautomation import FileInfo, PresetBD, PresetFLAC, VPath

from project_module import encoder as enc
from project_module import flt

core = vs.core


shader_file = 'assets/FSRCNNX_x2_56-16-4-1.glsl'
if not Path(shader_file).exists():
    hookpath = r"mpv/shaders/FSRCNNX_x2_16-0-4-1.glsl"
    shader_file = os.path.join(str(os.getenv("APPDATA")), hookpath)


# Sources
JP_BD = FileInfo(r"E:/src/[神的记事本][Heaven's Memo Pad][神様のメモ帳][BDMV]/神様のメモ帳_1/KAMIMEMO_01/BDMV/STREAM/00001.m2ts",
                 (66052, 68209), idx=lambda x: source(x), preset=[PresetBD, PresetFLAC])
JP_BD.name_file_final = VPath(fr"premux/{JP_BD.name} (Premux).mkv")
JP_BD.a_src_cut = VPath(JP_BD.name)


zones: Dict[Tuple[int, int], Dict[str, Any]] = {  # Zones for the encoder
    (0, 2156): {'b': 0.90}
}


def filterchain() -> Union[vs.VideoNode, Tuple[vs.VideoNode, ...]]:
    """Main filterchain"""
    import debandshit as dbs
    import EoEfunc as eoe
    import havsfunc as haf
    import rekt
    import vardefunc as vdf
    from vsutil import depth, get_y

    src = JP_BD.clip_cut
    rkt = rekt.rektlvls(src, [0, -1], [17, 17], [0, 1, 2, 3, 4, 6], [16, 4, -1, 2, 1, 1])
    rkt = rekt.rektlvls(rkt, None, None, [-1, -2, -3, -4, -5, -7], [13, 6, -1, 2, 1, 1])
    rkt = depth(rkt, 16)

    # Denoise
    stab = haf.SMDegrain(rkt, tr=3, thSAD=40, plane=0, Str=3.0)
    den_y = eoe.dn.BM3D(stab, sigma=[0.75, 0], radius=3)
    decs = vdf.noise.decsiz(den_y, sigmaS=8.0, min_in=200 << 8, max_in=236 << 8)

    # Debanding
    ret_y = core.retinex.MSRCP(get_y(decs), sigma=[50, 200, 350], upper_thr=0.005)
    pre_den = core.dfttest.DFTTest(ret_y, sigma=1.0, planes=[0])
    detail_mask = flt.detail_mask(pre_den, sigma=6, detail_brz=500, lines_brz=1500)

    deband = core.average.Mean([
        dbs.dumb3kdb(decs, radius=18, threshold=[24, 16], grain=[18, 6]),
        dbs.dumb3kdb(decs, radius=21, threshold=[36, 24], grain=[24, 12]),
        flt.placebo_debander(decs, iterations=2, threshold=3.25, radius=14, grain=4)
    ]).std.MaskedMerge(decs, detail_mask)

    grain = vdf.noise.Graigasm(
        thrs=[x << 8 for x in (32, 80, 128, 176)],
        strengths=[(0.15, 0.0), (0.10, 0.0), (0.05, 0.0), (0.0, 0.0)],
        sizes=(1.25, 1.20, 1.15, 1),
        sharps=(50, 40, 25, 0),
        grainers=[
            vdf.noise.AddGrain(seed=69420, constant=False),
            vdf.noise.AddGrain(seed=69420, constant=False),
            vdf.noise.AddGrain(seed=69420, constant=True)
        ]).graining(deband)

    return grain


if __name__ == '__main__':
    FILTERED = filterchain()
    enc.Encoder(JP_BD, FILTERED).run(zones=zones, flac=True),  # type: ignore
elif __name__ == '__vapoursynth__':
    FILTERED = filterchain()
    if not isinstance(FILTERED, vs.VideoNode):
        raise ImportError(f"Input clip has multiple output nodes ({len(FILTERED)})! Please output just 1 clip")
    else:
        enc.dither_down(FILTERED).set_output(0)
else:
    JP_BD.clip_cut.std.SetFrameProp('node', intval=0).text.Text('src').set_output(0)
    FILTERED = filterchain()
    if not isinstance(FILTERED, vs.VideoNode):
        for i, clip_filtered in enumerate(FILTERED, start=1):
            clip_filtered.std.SetFrameProp('node', intval=i).set_output(i)
    else:
        FILTERED.std.SetFrameProp('node', intval=1).set_output(1)
