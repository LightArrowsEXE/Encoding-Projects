from typing import Any, Dict, Tuple, Union

import vapoursynth as vs
from lvsfunc.misc import source
from vardautomation import FileInfo, PresetWEB, PresetAAC, VPath

from project_module import encoder as enc
from project_module import flt

core = vs.core


cuda = __name__ == '__main__'


# Sources
WEB_AV1 = FileInfo(r'src/kaguya3-pv_av1.mkv', idx=lambda x: source(x, force_lsmas=True, cachedir=''),
                   preset=[PresetWEB, PresetAAC])
WEB_H264 = FileInfo(r'src/kaguya3-pv_h264.mkv')
WEB_VP9 = FileInfo(r'src/kaguya3-pv_vp9.mkv', idx=lambda x: source(x, force_lsmas=True, cachedir=''))
WEB_AV1.name_file_final = VPath(fr"premux/{WEB_AV1.name} (Premux).mkv")
WEB_AV1.a_src_cut = WEB_AV1.name
WEB_AV1.do_qpfile = True


zones: Dict[Tuple[int, int], Dict[str, Any]] = {  # Zones for x265
}


def filterchain() -> Union[vs.VideoNode, Tuple[vs.VideoNode, ...]]:
    """Main VapourSynth filterchain"""
    import havsfunc as haf
    import lvsfunc as lvf
    import vardefunc as vdf
    from vsutil import depth

    av1 = WEB_AV1.clip_cut
    h264 = WEB_H264.clip_cut
    vp9 = WEB_VP9.clip_cut

    srcs = [av1, h264, vp9]
    avg = core.average.Mean(srcs)
    pick = flt.bestframeselect(srcs, avg)
    pick = depth(pick, 32)

    debl = lvf.deblock.vsdpir(pick, matrix=1, cuda=cuda)
    debl = depth(debl, 16)

    halo_mask = lvf.mask.halo_mask(debl, rad=1, brz=0.85, thmi=0.35, thma=0.95)
    halo_mask = halo_mask.std.Maximum().std.Inflate()

    bidehalo = lvf.dehalo.bidehalo(debl, sigmaR=8/255, sigmaS=2.0, sigmaS_final=1.5)
    dehalo_den = core.dfttest.DFTTest(bidehalo, sigma=8.0)
    dehalo_clean = haf.EdgeCleaner(dehalo_den, strength=8, smode=1, hot=True)

    dehalo = core.std.MaskedMerge(debl, dehalo_clean, halo_mask)

    deband = flt.masked_f3kdb(dehalo, rad=18, thr=[28, 20])

    grain = vdf.noise.Graigasm(
        thrs=[x << 8 for x in (32, 80, 128, 176)],
        strengths=[(0.20, 0.0), (0.15, 0.0), (0.10, 0.0), (0.0, 0.0)],
        sizes=(1.20, 1.15, 1.10, 1),
        sharps=(70, 60, 50, 50),
        grainers=[
            vdf.noise.AddGrain(seed=69420, constant=True),
            vdf.noise.AddGrain(seed=69420, constant=True),
            vdf.noise.AddGrain(seed=69420, constant=True)
        ]).graining(deband)

    return grain


if __name__ == '__main__':
    FILTERED = filterchain()
    enc.Encoder(WEB_AV1, FILTERED).run(clean_up=True, zones=zones)  # type: ignore
elif __name__ == '__vapoursynth__':
    FILTERED = filterchain()
    if not isinstance(FILTERED, vs.VideoNode):
        raise ImportError(
            f"Input clip has multiple output nodes ({len(FILTERED)})! Please output just 1 clip"
        )
    else:
        enc.dither_down(FILTERED).set_output(0)
else:
    WEB_AV1.clip_cut.std.SetFrameProp('node', intval=0).set_output(0)
    FILTERED = filterchain()
    if not isinstance(FILTERED, vs.VideoNode):
        for i, clip_filtered in enumerate(FILTERED, start=1):
            clip_filtered.std.SetFrameProp('node', intval=i).set_output(i)
    else:
        FILTERED.std.SetFrameProp('node', intval=1).set_output(1)
