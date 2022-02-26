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
JP_BD = FileInfo(r'BDMV/[BDMV][アニメ][171129] 「終物語」 第七巻／ひたぎランデブー/BD_VIDEO/BDMV/STREAM/00001.m2ts',
                 (None, -74), idx=lambda x: source(x, cachedir=''), preset=[PresetBD, PresetAAC])
JP_NCOP = FileInfo(r'BDMV/[BDMV][アニメ][171129] 「終物語」 第七巻／ひたぎランデブー/BD_VIDEO/BDMV/STREAM/00008.m2ts',
                   (12, -24), idx=lambda x: source(x, cachedir=''))
JP_NCED = FileInfo(r'BDMV/[BDMV][アニメ][171129] 「終物語」 第七巻／ひたぎランデブー/BD_VIDEO/BDMV/STREAM/00009.m2ts',
                   (12, -24), idx=lambda x: source(x, cachedir=''))
JP_BD.name_file_final = VPath(fr"premux/{JP_BD.name} (Premux).mkv")
JP_BD.a_src_cut = VPath(f"{JP_BD.name}_trim")
JP_BD.do_qpfile = True


# OP/ED scenefiltering
opstart = 2638
edstart = 28868
op_offset = 1
ed_offset = 1


edgefix_ranges: Iterable[Range] = [  # Ranges to perform edgefixing on
]

blurry_scaling: Iterable[Range] = [  # Ranges for blurrier scaling to avoid haloing/ringing
]

interp_ranges: Iterable[Range] = [  # QTGMC interpolation for certain scenes with shimmering
    (1951, 2094)
]

stronger_aa: Iterable[Range] = [
]

super_strong_aa: Iterable[Range] = [
]

sharpen_ranges: Iterable[Range] = [  # Ranges for artificial sharpening
]

sharpen_textures: Iterable[Range] = [  # Ranges for artificial sharpening of textures
]

sharp_reds: Iterable[Range] = [  # Sharpen reds in specific scenes
]

weaker_deband: Iterable[Range] = [  # Ranges for weaker (but still relatively strong) debanding
    (opstart+1962, opstart+2158), (2179, 2394), (7238, 7285), (8768, 8803)
]


# Disable filter ranges
no_denoising: Iterable[Range] = [
    (opstart+1385, opstart+1415), (opstart+1962, opstart+2158), (7238, 7285), (7478, 7519), (7562, 7597), (8768, 8803)
]

no_decsize: Iterable[Range] = [
]

no_debanding: Iterable[Range] = [
    (opstart+1385, opstart+1415), (opstart+1962, opstart+2158)
]

no_filtering: Iterable[Range] = [
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
    from vsutil import depth, get_y, insert_clip, iterate, join, plane, split

    src = JP_BD.clip_cut
    src_ncop, src_nced = JP_NCOP.clip_cut, JP_NCED.clip_cut
    src_ncop = src_ncop + src_ncop[-1]
    src_nced = src_nced + src_nced[-1]

    # OP/ED stack comps to check that it lines up
    # op_scomp = lvf.scomp(src[opstart:opstart+src_NCOP.num_frames-1]+b, masked_NCOP[:-op_offset]+b)  # noqa
    # ed_scomp = lvf.scomp(src[edstart:edstart+src_NCED.num_frames-1]+b, src_NCED[:-ed_offset]+b)  # noqa

    # Splicing in NCs and diff'ing back the credits
    spliced_ncs = insert_clip(src, src_ncop[:-op_offset], opstart)
    spliced_ncs = insert_clip(spliced_ncs, src_nced[:-ed_offset], edstart)

    den_src, den_ncs = map(core.dfttest.DFTTest, [src, spliced_ncs])
    den_src, den_ncs = depth(den_src, 32), depth(den_ncs, 32)
    diff = core.std.MakeDiff(den_src, den_ncs).dfttest.DFTTest(sigma=20.0, tbsize=5, tosize=3)

    # Edgefixing
    rkt = rekt.rektlvls(spliced_ncs, [0, 1079], [15, 15], [0, 1919], [15, 17])
    bb = bbmod(rkt, left=2, blur=32, y=False)
    bb = lvf.rfs(spliced_ncs, bb, edgefix_ranges)

    # Letterboxing edgefixing
    src_crop = core.std.CropRel(spliced_ncs, bottom=132, top=132)
    rkt_crop = rekt.rektlvls(src_crop, [0, 1, src_crop.height-2, src_crop.height-1], [3, -4, -4, 3])
    bb_crop = bbmod(rkt_crop, bottom=2, blur=50)
    pad = core.std.AddBorders(bb_crop, top=132, bottom=132, color=[16, 128, 128])

    bb = flt.auto_lbox(spliced_ncs, bb, pad)
    bb = depth(bb, 16)

    # Rescaling, detail mask finalising
    scaled, descale_mask = flt.rescaler(bb, 720, shader_file, blurry_scale_ranges=blurry_scaling)
    blank_clip = core.std.BlankClip(descale_mask)
    descale_mask = lvf.rfs(descale_mask, blank_clip, [(opstart, opstart+src_ncop.num_frames),
                                                      (edstart, edstart+src_nced.num_frames)])

    # Fixing fucked scaling during letterbox scenes
    blank = core.std.BlankClip(scaled).std.Invert()
    wh_crop = blank.std.CropRel(top=138, bottom=138)
    wh_pad = core.std.AddBorders(wh_crop, top=138, bottom=138)

    letterbox_scale = core.std.MaskedMerge(bb, scaled, wh_pad)
    scaled = flt.auto_lbox(scaled, scaled, letterbox_scale)

    # Mostly regular filtering from this point onward
    line_mask = core.std.Prewitt(scaled, scale=2)
    den_detail_mask = flt.detail_mask(bb, pf_sigma=2, brz=(3500, 6000))

    dft_y = core.dfttest.DFTTest(scaled, sigma=2.0, tbsize=5, tosize=3, planes=[0, 1])
    bm3d = lvf.denoise.bm3d(scaled, sigma=[1.5, 1.25], radius=5, ref=dft_y)
    bm3d = join([plane(bm3d, 0), plane(bm3d, 1), plane(scaled, 2)])
    dft = core.std.MaskedMerge(bm3d, scaled, den_detail_mask, planes=[0, 1])

    ccd_uv = ccd(dft, threshold=6, matrix='709')
    ccdm = core.std.MaskedMerge(ccd_uv, dft, line_mask, planes=[1, 2])

    csharp_den = eoe.misc.ContraSharpening(ccdm, scaled, rep=4)
    csharp_den = core.std.Expr([ccdm, csharp_den], "x y min")

    no_den = lvf.rfs(csharp_den, scaled, no_denoising)
    decs = vdf.noise.decsiz(no_den, sigmaS=1, min_in=224 << 8, max_in=245 << 8)
    decs = lvf.rfs(decs, no_den, no_decsize)

    # Sharpen reds, dehalo greens. Only useful for scenes where the red lineart tends to get debanded away tbf
    blurred_clip = core.std.Convolution(decs, matrix=[1, 2, 1, 2, 4, 2, 1, 2, 1])
    blur_green = core.std.Expr([decs, blurred_clip], ['', '', 'x 0.009 < y x ?'])
    unsharp = core.std.Expr([decs, blurred_clip], expr=['', '', 'x y - 1.15 * x +'])
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

    # Sharpen textures through the unsharpening technique
    line_mask = vdf.mask.FDOG().get_mask(get_y(sharpen)).std.Binarize(48 << 8).std.Inflate().std.Maximum().std.Maximum()
    blurred_clip = core.std.Convolution(sharpen, matrix=[1, 1, 1, 1, 1, 1, 1, 1, 1])
    unsharp_textures = core.std.Expr([sharpen, blurred_clip], 'x y - 1.05 * x +')
    unsharp_textures = core.std.MaskedMerge(unsharp_textures, sharpen, line_mask)
    unsharp_textures = lvf.rfs(sharpen, unsharp_textures, sharpen_textures)

    # Trying to forcibly clean up remaining noise/bleeds/ringing around edges
    clean_edge_y = haf.EdgeCleaner(unsharp_textures, strength=6.5, smode=1)
    clean_edge_uv = [haf.EdgeCleaner(c, strength=10, smode=1) for c in split(unsharp_textures)[1:]]
    clean_edge = join([clean_edge_y, clean_edge_uv[0], clean_edge_uv[1]])

    # >SHAFT CGI and camera fuckery
    interp = haf.QTGMC(clean_edge, TFF=True, TR0=0, TR1=2, TR2=3, Preset="Placebo", SourceMatch=0,
                       Lossless=2, MatchEnhance=0.8, NoiseProcess=0, FPSDivisor=2)
    interp = lvf.rfs(clean_edge, interp, interp_ranges)

    credit_clean = core.dfttest.DFTTest(bb, sigma=20.0, tbsize=5, tosize=3, planes=[0])
    credit_clean = core.dfttest.DFTTest(credit_clean, sigma=25.0, tbsize=5, tosize=3, planes=[1, 2])
    credit_merge = core.std.MaskedMerge(interp, credit_clean, descale_mask)

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
        strengths=[(0.25, 0.0), (0.20, 0.0), (0.15, 0.0), (0.0, 0.0)],
        sizes=(1.0, 1.0, 1.0, 1.0),
        sharps=(60, 50, 45, 0),
        grainers=[
            vdf.noise.AddGrain(seed=69420, constant=True),
            vdf.noise.AddGrain(seed=69420, constant=True),
            vdf.noise.AddGrain(seed=69420, constant=False)
        ]).graining(deband)

    # Merge back credits
    merge_creds = core.std.MergeDiff(depth(grain, 32), diff)
    no_filter = lvf.rfs(merge_creds, depth(bb, 32), no_filtering)

    return no_filter


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
