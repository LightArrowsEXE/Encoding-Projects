from typing import Tuple, Union

import vapoursynth as vs
from lvsfunc.misc import source
from vardautomation import FileInfo, PresetAAC, PresetWEB, VPath

from project_module import enc, flt

core = vs.core


use_cuda: bool = __name__ == '__main__'


# Sources
JP_BD = FileInfo(r'src/fate project 2021.dgi', [(165411, 166311)],
                 idx=lambda x: source(x), preset=[PresetWEB, PresetAAC])
JP_BD.name_file_final = VPath(f"premux/{JP_BD.name} (Premux).mkv")
JP_BD.a_src = VPath(JP_BD.path_without_ext.to_str() + "_track_1.aac")
JP_BD.do_qpfile = True


def filterchain() -> Union[vs.VideoNode, Tuple[vs.VideoNode, ...]]:
    """Main VapourSynth filterchain"""
    import EoEfunc as eoe
    import havsfunc as haf
    import lvsfunc as lvf
    import vardefunc as vdf
    from vsutil import depth

    src = JP_BD.clip_cut
    yt = lvf.src(r"src/『魔法使いの夜』ティザーPV-NHIgc-seeSo.mkv", ref=src) \
        .std.AssumeFPS(fpsnum=24000, fpsden=1001)
    src = core.std.SetFrameProp(src, '_FieldBased', intval=0)
    se = core.tivtc.TDecimate(src)

    # Fix range compression and missing frame in TV release
    csp = core.resize.Bicubic(se, range_in=0, range=1, dither_type="error_diffusion")
    csp = csp.std.SetFrameProp(prop="_ColorRange", intval=1)
    merge = csp[:400] + yt[400] + csp[400:]

    # "Delogoing" and "Edgefixing"
    sqmask = lvf.mask.BoundingBox((1753, 27), (118, 50)).get_mask(merge).std.Inflate().std.Inflate().std.Maximum()
    sqmask = sqmask.std.Maximum().std.Maximum().std.Median().std.Convolution([1] * 9).std.Convolution([1] * 9)

    mask_merge = core.std.MaskedMerge(merge, yt[:merge.num_frames], sqmask)

    sqmask_ef = lvf.mask.BoundingBox((3, 3), (src.width-3, src.height-3)).get_mask(mask_merge)
    ef = core.std.MaskedMerge(yt, mask_merge, sqmask_ef)
    ef = depth(ef, 16)

    debl = lvf.deblock.vsdpir(ef, strength=35, cuda=use_cuda)
    csharp = eoe.misc.ContraSharpening(debl, ef, radius=2, rep=13)
    darken = haf.FastLineDarkenMOD(csharp, strength=24)

    deband = core.average.Mean([
        flt.masked_f3kdb(darken, rad=16, thr=[28, 20], grain=[16, 6]),
        flt.masked_placebo(darken, rad=14, thr=4.5, itr=2, grain=2)
    ])

    grain = vdf.noise.Graigasm(
        thrs=[x << 8 for x in (32, 80, 128, 176)],
        strengths=[(0.15, 0.0), (0.10, 0.0), (0.05, 0.0), (0.0, 0.0)],
        sizes=(1.15, 1.10, 1.05, 1),
        sharps=(100, 90, 80, 50),
        grainers=[
            vdf.noise.AddGrain(seed=69420, constant=True),
            vdf.noise.AddGrain(seed=69420, constant=False),
            vdf.noise.AddGrain(seed=69420, constant=False)
        ]).graining(deband)

    return grain


if __name__ == '__main__':
    FILTERED = filterchain()
    enc.Encoder(JP_BD, FILTERED).run(clean_up=True, settings='x265_settings')
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
