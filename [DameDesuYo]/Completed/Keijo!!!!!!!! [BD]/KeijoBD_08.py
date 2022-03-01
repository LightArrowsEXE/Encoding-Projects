from __future__ import annotations

import multiprocessing as mp
from functools import partial
from typing import Any, Dict, List, Tuple


import vapoursynth as vs
import yaml
from lvsfunc.misc import source
from lvsfunc.types import Range
from vardautomation import FileInfo, PresetBD, VPath, get_vs_core
from vardefunc import initialise_input

from project_module import encoder as enc
from project_module import flt

with open("config.yaml", 'r') as conf:
    config = yaml.load(conf, Loader=yaml.FullLoader)

core = get_vs_core(range(0, (mp.cpu_count() - 2)) if config['reserve_core'] else None)

# Sources
JP_BD = FileInfo(f"{config['bdmv_dir']}/[BDMV][Keijo!!!!!!!!][Vol.4]/BDMV/STREAM/00001.m2ts", (None, -24),
                 idx=lambda x: source(x, force_lsmas=True, cachedir=''), preset=[PresetBD])
JP_NCOP = FileInfo(f"{config['bdmv_dir']}/[BDMV][Keijo!!!!!!!!][Vol.3]/BDMV/STREAM/00014.m2ts", (None, -24),
                   idx=lambda x: source(x, force_lsmas=True, cachedir=''))
JP_NCED = FileInfo(f"{config['bdmv_dir']}/[BDMV][Keijo!!!!!!!!][Vol.1]/BDMV/STREAM/00007.m2ts", (24, -24),
                   idx=lambda x: source(x, force_lsmas=True, cachedir=''))
JP_BD.name_file_final = enc.parse_name(config, __file__)
JP_BD.a_src_cut = VPath(JP_BD.name)


# OP/ED start times
opstart = 600
edstart = 31770
op_offset = 1
ed_offset = 2

# Scenefiltering
chroma_denoise: List[Range] = [  # ccd on certain ranges with chroma noise
]


zones: Dict[Tuple[int, int], Dict[str, Any]] = {  # Zones for the encoder
}


if opstart is not False:
    chroma_denoise += [(opstart+1081, opstart+1124)]


@initialise_input()
def filterchain(src: vs.VideoNode = JP_BD.clip_cut,
                ncop: vs.VideoNode = JP_NCOP.clip_cut,
                nced: vs.VideoNode = JP_NCED.clip_cut
                ) -> vs.VideoNode | Tuple[vs.VideoNode, ...]:
    """Main filterchain"""
    import EoEfunc as eoe
    import havsfunc as haf
    import lvsfunc as lvf
    import vardefunc as vdf
    from ccd import ccd
    from vsutil import depth, insert_clip

    assert src.format
    assert ncop.format
    assert nced.format

    src_c = src
    b = core.std.BlankClip(src, length=1)

    ncop = vdf.util.initialise_clip(ncop)
    nced = vdf.util.initialise_clip(nced)

    diff_rfs: List[Range] = []

    # OP/ED stack comps to check if they line up, as well as splicing them in
    return_scomp = []
    if opstart is not False:
        op_scomp = lvf.scomp(src[opstart:opstart+ncop.num_frames-1]+b, ncop[:-op_offset]+b)  # noqa
        diff_rfs += [(opstart, opstart+opstart+ncop.num_frames-1-op_offset)]
        src = insert_clip(src, ncop[:-op_offset], opstart)
        return_scomp += [op_scomp]
    if edstart is not False:
        ed_scomp = lvf.scomp(src[edstart:edstart+nced.num_frames-1]+b, nced[:-ed_offset]+b)  # noqa
        diff_rfs += [(edstart, edstart+opstart+nced.num_frames-1-ed_offset)]
        src = insert_clip(src, nced[:-ed_offset], edstart)
        return_scomp += [ed_scomp]

    return_scomp += [src]

    # Make diff for credits
    den_src, den_ncs = map(partial(core.dfttest.DFTTest, sigma=5), [src_c, src])
    den_src, den_ncs = depth(den_src, 32), depth(den_ncs, 32)
    diff = core.std.MakeDiff(den_src, den_ncs).dfttest.DFTTest(sigma=20.0)

    # For some reason there's noise from previous credits remaining? Removing that here
    diff_brz = vdf.misc.merge_chroma(depth(depth(diff.std.Binarize(0.025), 16).rgvs.RemoveGrain(3), 32), diff)
    diff = core.std.Expr([diff, diff_brz], "x y min")

    # And somehow it creates weird values in some places? Limiting here except for OP/ED
    diff_lim = diff.std.Limiter(0, 0)
    diff = lvf.rfs(diff_lim, diff, diff_rfs)

    return_scomp += [diff]
    # return return_scomp

    # Denoising. This BD has very ugly compression artefacting (looks sharpened?)
    smd = haf.SMDegrain(src, tr=3, thSAD=50)
    ref = smd.dfttest.DFTTest(slocation=[0.0, 4, 0.25, 16, 0.3, 512, 1.0, 512], planes=[0], **eoe.freq._dfttest_args)
    bm3d = lvf.denoise.bm3d(smd, sigma=[0.65, 0], radius=3, ref=ref)

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

    merge_creds = core.std.MergeDiff(depth(deband, 32), diff)

    return merge_creds


if __name__ == '__main__':
    FILTERED = filterchain()
    enc.Encoder(JP_BD, FILTERED).run(zones=zones, flac=True)  # type: ignore
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
