import multiprocessing as mp
from typing import Any, Dict, List, Tuple, Union

import vapoursynth as vs
from lvsfunc.misc import source
from lvsfunc.types import Range
from vardautomation import FileInfo, PresetBD, PresetFLAC, VPath, get_vs_core
from vardefunc import initialise_input

from project_module import encoder as enc
from project_module import flt

core = get_vs_core(range(0, mp.cpu_count(), 2))


# Sources
JP_BD = FileInfo(r'E:/src/[BDMV][Keijo!!!!!!!!][Vol.1-3]/KEIJO_3/BDMV/STREAM/00014.m2ts',  # noqa
                 (None, -24), idx=lambda x: source(x, force_lsmas=True, cachedir=''), preset=[PresetBD, PresetFLAC])
JP_BD.name_file_final = VPath(fr"premux/{JP_BD.name} (Premux).mkv")
JP_BD.a_src_cut = VPath(JP_BD.name)


# OP/ED start times
opstart = 0
edstart = False

# Scenefiltering
chroma_denoise: List[Range] = [  # ccd on certain ranges with chroma noise
]


zones: Dict[Tuple[int, int], Dict[str, Any]] = {  # Zones for the encoder
}


if opstart is not False:
    chroma_denoise += [(opstart+1081, opstart+1124)]


@initialise_input(bits=16)
def filterchain(src: vs.VideoNode = JP_BD.clip_cut) -> Union[vs.VideoNode, Tuple[vs.VideoNode, ...]]:
    """Main filterchain"""
    import EoEfunc as eoe
    import havsfunc as haf
    import lvsfunc as lvf
    import vardefunc as vdf
    from ccd import ccd

    # Denoising. This BD has very ugly compression artefacting (looks sharpened?)
    smd = haf.SMDegrain(src, tr=3, thSAD=50)
    ref = smd.dfttest.DFTTest(slocation=[0.0, 4, 0.25, 16, 0.3, 512, 1.0, 512], planes=[0], **eoe.freq._dfttest_args)
    bm3d = lvf.denoise.bm3d(smd, sigma=[1.0, 0], radius=3, ref=ref)

    den_uv = ccd(bm3d, threshold=6)
    den_uv = lvf.rfs(bm3d, den_uv, chroma_denoise)

    decs = vdf.noise.decsiz(den_uv, sigmaS=12, min_in=192 << 8, max_in=236 << 8)

    # AA and lineart warping. I'm fairly sure the lineart was sharpened, with some kind of dehalo applied?
    aa = flt.obliaa(decs, eedi3_args={'alpha': 0.05, 'beta': 0.85, 'gamma': 200})
    aa_min = core.std.Expr([aa, core.rgvs.Repair(aa, decs, 13)], "x y min")
    desharp = aa_min.warp.AWarpSharp2(thresh=96, blur=3, type=1, depth=-1, planes=[0])

    # Chroma fixes by warping.
    cwarp = desharp.warp.AWarpSharp2(thresh=88, blur=3, type=1, depth=4, planes=[1, 2])

    # Debanding.
    deband = flt.masked_f3kdb(cwarp, thr=[28, 24], grain=[16, 12])

    return deband


if __name__ == '__main__':
    FILTERED = filterchain()
    enc.Patcher(JP_BD, FILTERED).patch(ranges=[(1037, 1060), (2113, None)],
                                       external_file="premux/KeijoBD_NCOP1v1 (Premux).mkv")
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
