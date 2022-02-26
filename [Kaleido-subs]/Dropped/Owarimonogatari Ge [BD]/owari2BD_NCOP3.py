import os
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple, Union

import vapoursynth as vs
from lvsfunc.misc import source
from lvsfunc.types import Range
from vardautomation import FileInfo, PresetAAC, PresetBD, VPath

from project_module import encoder as enc
from project_module import flt

core = vs.core


shader_file = 'assets/FSRCNNX_x2_56-16-4-1.glsl'
if not Path(shader_file).exists():
    hookpath = r"mpv/shaders/FSRCNNX_x2_56-16-4-1.glsl"
    shader_file = os.path.join(str(os.getenv("APPDATA")), hookpath)


# Sources
JP_BD = FileInfo(r'BDMV/[BDMV][アニメ][171227] 「終物語」 第八巻／おうぎダーク/BD_VIDEO/BDMV/STREAM/00010.m2ts',
                 (12, -24), idx=lambda x: source(x, cachedir=''), preset=[PresetBD, PresetAAC])
JP_BD.name_file_final = VPath(fr"premux/{JP_BD.name} (Premux).mkv")
JP_BD.a_src_cut = VPath(f"{JP_BD.name}_trim")
JP_BD.do_qpfile = True


# Other filtering ranges
edgefix_ranges: Iterable[Range] = [  # Ranges to perform edgefixing on
]

blurry_scaling: Iterable[Range] = [  # Ranges for blurrier scaling to avoid haloing/ringing
]

stronger_aa: Iterable[Range] = [
]

super_strong_aa: Iterable[Range] = [
]

sharpen_ranges: Iterable[Range] = [  # Ranges for artificial sharpening
]

sharp_reds: Iterable[Range] = [  # Sharpen reds in specific scenes
    (None, None)
]

weaker_deband: Iterable[Range] = [  # Ranges for weaker (but still relatively strong) debanding
]

# Disable filter ranges
no_denoising: Iterable[Range] = [
]

no_debanding: Iterable[Range] = [
]

zones: Dict[Tuple[int, int], Dict[str, Any]] = {  # Zones for x265
}


def filterchain() -> Union[vs.VideoNode, Tuple[vs.VideoNode, ...]]:
    """Main VapourSynth filterchain"""
    import EoEfunc as eoe
    import havsfunc as haf
    import lvsfunc as lvf
    import rekt
    import vardefunc as vdf
    from awsmfunc import bbmod
    from ccd import ccd
    from debandshit import dumb3kdb
    from vsutil import depth, iterate, join, plane, split

    src = JP_BD.clip_cut

    rkt = rekt.rektlvls(src, [0, 1079], [15, 15], [0, 1919], [15, 17])
    bb = bbmod(rkt, left=2, blur=32, y=False)
    bb = lvf.rfs(src, bb, edgefix_ranges)
    bb = depth(bb, 16)

    # Rescaling, detail mask finalising
    scaled, descale_mask = flt.rescaler(bb, 720, shader_file, blurry_scale_ranges=blurry_scaling)

    line_mask = core.std.Prewitt(scaled, scale=2)
    den_detail_mask = flt.detail_mask(bb, pf_sigma=2, brz=(3500, 6000))

    dft_y = core.dfttest.DFTTest(scaled, sigma=2.0, tbsize=5, tosize=3, planes=[0, 1])
    bm3d = lvf.denoise.bm3d(scaled, sigma=[1.5, 1.25], radius=5, ref=dft_y)
    bm3d = join([plane(bm3d, 0), plane(bm3d, 1), plane(scaled, 2)])
    dft = core.std.MaskedMerge(bm3d, scaled, den_detail_mask, planes=[0, 1])

    ccd_uv = ccd(dft, threshold=6, matrix='709')
    ccdm = core.std.MaskedMerge(ccd_uv, dft, line_mask, planes=[1, 2])

    no_den = lvf.rfs(ccdm, scaled, no_denoising)
    decs = vdf.noise.decsiz(no_den, sigmaS=1, min_in=224 << 8, max_in=245 << 8)

    # Sharpen reds, dehalo greens. Only useful for scenes where the red lineart tends to get debanded away tbf
    blurred_clip = core.std.Convolution(decs, matrix=[1, 2, 1, 2, 4, 2, 1, 2, 1])
    blur_green = core.std.Expr([decs, blurred_clip], ['', '', 'x 0.009 < y x ?'])
    unsharp = core.std.Expr(clips=[decs, blurred_clip], expr=['', '', 'x y - 1.15 * x +'])
    gr_dehalo_expr = core.std.Expr([unsharp, blur_green], ['', '', 'x 0.009 < y x ?'])
    gr_dehalo_mask = core.std.MaskedMerge(decs, gr_dehalo_expr, line_mask, planes=[2])

    sharpen_red_lines = lvf.rfs(decs, gr_dehalo_mask, sharp_reds)

    sq_mask = lvf.mask.BoundingBox((2, 2), (src.width-4, src.height-4)).get_mask(sharpen_red_lines)
    csharp = eoe.misc.ContraSharpening(sharpen_red_lines, scaled, rep=4)
    csharp_v = eoe.misc.ContraSharpening(csharp, scaled, rep=17, planes=[2])

    baa = lvf.aa.based_aa(csharp_v, str(shader_file))
    sraa = lvf.sraa(csharp_v, rfactor=1.4, downscaler=lvf.kernels.Bicubic(b=-1/2, c=1/4).scale)
    clmp = lvf.aa.clamp_aa(csharp_v, baa, sraa, strength=1.35)

    sraa_strong = lvf.sraa(csharp_v, rfactor=1.3, downscaler=lvf.kernels.Bicubic(b=-1/2, c=1/4).scale)
    clmp_strong = lvf.aa.clamp_aa(csharp_v, baa, sraa_strong, strength=1.75)

    trans_sraa = flt.transpose_sraa(csharp_v, rfactor=1.2, downscaler=lvf.kernels.Bicubic(b=-1/2, c=1/4).scale)

    clmp = lvf.rfs(clmp, clmp_strong, stronger_aa)
    clmp = lvf.rfs(clmp, trans_sraa, super_strong_aa)

    # Weak artificial sharpening for very specific scenes
    sharpen = haf.LSFmod(clmp, strength=50, soft=10, edgemode=1, Smethod=2, Lmode=2, defaults='slow')
    sharpen = lvf.rfs(clmp, sharpen, sharpen_ranges)
    sharpen = core.std.MaskedMerge(decs, sharpen, sq_mask)

    # Trying to forcibly clean up remaining noise/bleeds/ringing around edges
    clean_edge_y = haf.EdgeCleaner(sharpen, strength=6.5)
    clean_edge_uv = [haf.EdgeCleaner(c, strength=10) for c in split(sharpen)[1:]]
    clean_edge = join([clean_edge_y, clean_edge_uv[0], clean_edge_uv[1]])

    credit_clean = core.dfttest.DFTTest(bb, sigma=20.0, tbsize=5, tosize=3, planes=[0])
    credit_clean = core.dfttest.DFTTest(credit_clean, sigma=25.0, tbsize=5, tosize=3, planes=[1, 2])
    credit_merge = core.std.MaskedMerge(clean_edge, credit_clean, descale_mask)

    # Debanding + masking
    darken = flt.line_darkening(credit_merge, strength=0.25)
    detail_mask = flt.detail_mask(darken, brz=(500, 600))
    line_mask = core.std.Prewitt(darken, scale=1.5)
    exp_mask = iterate(line_mask, core.std.Inflate, 7)
    line_mask = core.std.Expr([line_mask, exp_mask], "y x -")

    deband = core.average.Mean([
        dumb3kdb(credit_merge, radius=18, threshold=[24, 24, 24], grain=[24, 24], seed=69420),
        dumb3kdb(credit_merge, radius=21, threshold=[36, 24, 24], grain=[40, 24], seed=69420),
        dumb3kdb(credit_merge, radius=24, threshold=[48, 24, 24], grain=[40, 24], seed=69420),
        flt.placebo_debander(credit_merge, radius=16, threshold=4.5, iterations=2, grain=8)])
    deband_masked = core.std.MaskedMerge(deband, credit_merge, detail_mask)

    deband_weaker = core.average.Mean([
        dumb3kdb(credit_merge, radius=18, threshold=[32, 24, 24], grain=[24, 24], seed=69420),
        flt.placebo_debander(credit_merge, radius=16, threshold=5.0, iterations=2, grain=8)])
    deband_weaker_masked = core.std.MaskedMerge(deband_weaker, credit_merge, detail_mask)

    deband = lvf.rfs(deband_masked, deband_weaker_masked, weaker_deband)
    deband = lvf.rfs(deband, credit_merge, no_debanding)

    grain = vdf.noise.Graigasm(
        thrs=[x << 8 for x in (32, 80, 128, 176)],
        strengths=[(0.15, 0.0), (0.10, 0.0), (0.05, 0.0), (0.0, 0.0)],
        sizes=(1.10, 1.10, 1.05, 1.0),
        sharps=(60, 50, 45, 0),
        grainers=[
            vdf.noise.AddGrain(seed=69420, constant=False),
            vdf.noise.AddGrain(seed=69420, constant=True),
            vdf.noise.AddGrain(seed=69420, constant=True)
        ]).graining(deband)

    return grain


if __name__ == '__main__':
    enc.Encoder(JP_BD, filterchain()).run(clean_up=True)  # type: ignore
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
