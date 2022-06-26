from __future__ import annotations

from typing import Any, Dict, List, Tuple

import vapoursynth as vs
import vsencode as vse
from lvsfunc.types import Range
from vardefunc import initialise_input

from project_module import flt

ini = vse.generate.init_project()

core = vse.util.get_vs_core(reserve_core=ini.reserve_core)

# Sources
JP_BD = vse.FileInfo(f"{ini.bdmv_dir}/[BDMV][Keijo!!!!!!!!][Vol.4]/BDMV/STREAM/00003.m2ts", (24, -24))


# OP/ED start times
edstart = 5581

# Scenefiltering
chroma_denoise: List[Range] = [  # ccd on certain ranges with chroma noise
]


zones: Dict[Tuple[int, int], Dict[str, Any]] = {  # Zones for the encoder
}


@initialise_input()
def filterchain(src: vs.VideoNode = JP_BD.clip_cut) -> vs.VideoNode | Tuple[vs.VideoNode, ...]:
    """Main filterchain"""
    import EoEfunc as eoe
    import havsfunc as haf
    import lvsfunc as lvf
    import vardefunc as vdf
    import jvsfunc as jvf

    # Denoising. This BD has very ugly compression artefacting (looks sharpened?)
    smd = haf.SMDegrain(src, tr=3, thSAD=50)
    ref = smd.dfttest.DFTTest(slocation=[0.0, 4, 0.25, 16, 0.3, 512, 1.0, 512], planes=[0], **eoe.freq._dfttest_args)
    bm3d = lvf.denoise.bm3d(smd, sigma=[0.65, 0], radius=3, ref=ref)

    den_uv = jvf.ccd(bm3d, threshold=6)
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

    final = lvf.rfs(deband, src, [(edstart or src.num_frames - 1, None)])

    return final


FILTERED = filterchain()


if __name__ == '__main__':
    vse.EncodeRunner(JP_BD, FILTERED).video('x265', '.settings/x265_settings', zones=zones) \
        .audio('flac').mux('LightArrowsEXE@DameDesuYo').run()
elif __name__ == '__vapoursynth__':
    if not isinstance(FILTERED, vs.VideoNode):
        raise vs.Error(f"Input clip has multiple output nodes ({len(FILTERED)})! Please output a single clip")
    else:
        vse.video.finalize_clip(FILTERED).set_output(0)
else:
    JP_BD.clip_cut.set_output(0)

    if not isinstance(FILTERED, vs.VideoNode):
        for i, clip_filtered in enumerate(FILTERED, start=1):
            clip_filtered.set_output(i)
    else:
        FILTERED.set_output(1)

    for i, audio_node in enumerate(JP_BD.audios_cut, start=10):
        audio_node.set_output(i)
