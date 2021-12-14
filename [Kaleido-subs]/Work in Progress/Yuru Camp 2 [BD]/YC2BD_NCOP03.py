import os
from pathlib import Path
from typing import Tuple, Union

import vapoursynth as vs
from lvsfunc.misc import source
from vardautomation import FileInfo, PresetAAC, PresetBD, VPath

from project_module import enc, flt

core = vs.core


shader_file = Path(r'assets/FSRCNNX_x2_56-16-4-1.glsl')
if not shader_file.exists:
    hookpath = r"mpv/shaders/FSRCNNX_x2_56-16-4-1.glsl"
    shader_file = os.path.join(os.getenv("APPDATA"), hookpath)


# Sources
JP_BD = FileInfo(r'BDMV/[BDMV][210728][Yuru Camp Season 2][Vol.3 Fin]/BD/BDMV/STREAM/00013.m2ts', [(24, -24)],
                 idx=lambda x: source(x, force_lsmas=True, cachedir=''), preset=[PresetBD, PresetAAC])
JP_EP = FileInfo(r'BDMV/[BDMV][210324][Yuru Camp Season 2][Vol.1]/BD/BDMV/STREAM/00007.m2ts', [(1558+24, 1558+2184)],
                 idx=lambda x: source(x, force_lsmas=True, cachedir=''))
JP_BD.name_file_final = VPath(f"premux/{JP_BD.name} (Premux).mkv")
JP_BD.a_src_cut = VPath(JP_BD.name)
JP_BD.do_qpfile = True


def filterchain() -> Union[vs.VideoNode, Tuple[vs.VideoNode, ...]]:
    """Main VapourSynth filterchain"""
    import EoEfunc as eoe
    import lvsfunc as lvf
    import vardefunc as vdf
    from ccd import ccd
    from finedehalo import fine_dehalo
    from vsutil import depth, get_y

    src, ep = JP_BD.clip_cut, JP_EP.clip_cut
    src = lvf.rfs(src, ep, [(811, 859)])
    src = depth(src, 16)

    # This noise can burn in hell.
    denoise_pre = get_y(src.dfttest.DFTTest(sigma=1.0))
    denoise_ret = core.retinex.MSRCP(denoise_pre, sigma=[50, 200, 350], upper_thr=0.005)
    denoise_mask = flt.detail_mask(denoise_ret, sigma=2.0, lines_brz=3000).rgvs.RemoveGrain(4)

    denoise_pre = core.dfttest.DFTTest(src, sigma=4.0)
    denoise_smd = eoe.dn.CMDegrain(src, tr=5, thSAD=275, freq_merge=True, prefilter=denoise_pre)
    denoise_masked = core.std.MaskedMerge(denoise_smd, src, denoise_mask)

    denoise_uv = ccd(denoise_masked, threshold=6)
    decs = vdf.noise.decsiz(denoise_uv, sigmaS=8, min_in=200 << 8, max_in=235 << 8)

    # FUCK THIS SHOW'S LINEART HOLY SHIT
    baa = lvf.aa.based_aa(decs.std.Transpose(), str(shader_file), gamma=120)
    baa = lvf.aa.based_aa(baa.std.Transpose(), str(shader_file), gamma=120)
    sraa = lvf.sraa(decs, rfactor=1.4)
    clmp_aa = lvf.aa.clamp_aa(decs, baa, sraa, strength=1.65)

    # AAing introduces some haloing (zzzzzz)
    restr_edges = fine_dehalo(clmp_aa, decs)
    restr_dark = core.std.Expr([clmp_aa, restr_edges], "x y min")

    deband = core.average.Mean([
        flt.masked_f3kdb(restr_dark, rad=17, thr=[28, 20], grain=[12, 8]),
        flt.masked_f3kdb(restr_dark, rad=21, thr=[36, 32], grain=[24, 12]),
        flt.masked_placebo(restr_dark, rad=6.5, thr=2.5, itr=2, grain=4)
    ])

    grain = vdf.noise.Graigasm(
        thrs=[x << 8 for x in (32, 80, 128, 176)],
        strengths=[(0.25, 0.0), (0.20, 0.0), (0.15, 0.0), (0.0, 0.0)],
        sizes=(1.20, 1.15, 1.10, 1),
        sharps=(80, 70, 60, 50),
        grainers=[
            vdf.noise.AddGrain(seed=69420, constant=True),
            vdf.noise.AddGrain(seed=69420, constant=False),
            vdf.noise.AddGrain(seed=69420, constant=False)
        ]).graining(deband)

    return grain


if __name__ == '__main__':
    FILTERED = filterchain()
    enc.Encoder(JP_BD, FILTERED).run(clean_up=True)
elif __name__ == '__vapoursynth__':
    FILTERED = filterchain()
    if not isinstance(FILTERED, vs.VideoNode):
        raise ImportError(
            f"Input clip has multiple output nodes ({len(FILTERED)})! Please output a single clip")
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
