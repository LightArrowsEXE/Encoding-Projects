from typing import Set, Tuple, Union

import vapoursynth as vs
from lvsfunc.misc import source
from vardautomation import FileInfo, PresetAAC, PresetBD, VPath
from vsgan import VSGAN

from project_module import encoder as enc
from project_module import flt

core = vs.core
core.num_threads = 4


# Sources
JP_DVD = FileInfo(r'BDMV/130208_JOSHIRAKU_OAD/VIDEO_TS/VTS_01_0.d2v', (26, -34),
                  idx=lambda x: source(x, rff=False), preset=[PresetBD, PresetAAC])
JP_BD_NCOP = FileInfo(r'BDMV/120926_JOSHIRAKU_VOL1/BDMV/STREAM/00001.m2ts', (24, -24),
                      idx=lambda x: source(x, cachedir=''))
JP_BD_NCED = FileInfo(r'BDMV/120926_JOSHIRAKU_VOL1/BDMV/STREAM/00002.m2ts', (24, -24),
                      idx=lambda x: source(x, cachedir=''))
JP_BD_03 = FileInfo(r'BDMV/121024_JOSHIRAKU_VOL2/BDMV/STREAM/00000.m2ts', (24, 34789),
                    idx=lambda x: source(x, cachedir=''))
JP_DVD.clip = core.std.AssumeFPS(JP_DVD.clip, fpsnum=24000, fpsden=1001)  # To get it to trim properly
JP_DVD.name_file_final = VPath(fr"premux/{JP_DVD.name} (Premux).mkv")
JP_DVD.a_src = VPath(r"BDMV/130208_JOSHIRAKU_OAD/VIDEO_TS/VTS_01_0 T80 stereo 448 kbps DELAY 0 ms.ac3")
JP_DVD.a_src_cut = VPath(f"{JP_DVD.name}_cut.ac3")
JP_DVD.do_qpfile = True


PROPS_DVD: Set[Tuple[str, int]] = {
    ('_ChromaLocation', 0),
    ('_Matrix', 6),
    ('_Transfer', 6),
    ('_Primaries', 6),
    ('_FieldBased', 0)
}

PROPS_BD: Set[Tuple[str, int]] = {
    ('_Matrix', 1),
    ('_Transfer', 1),
    ('_Primaries', 1)
}

vsgan = VSGAN('cuda')
vsgan.load_model('../assets/2xjoshiraku_500000_G.pth')

# OP/ED Variables
opstart = 0
edstart = 31888
op_offset = 1
ed_offset = 1


def filterchain() -> Union[vs.VideoNode, Tuple[vs.VideoNode, ...]]:
    """Main filterchain"""
    import havsfunc as haf
    import lvsfunc as lvf
    import muvsfunc as muf
    import debandshit as dbs
    import vardefunc as vdf
    from vsutil import depth, get_y, insert_clip, join, plane

    src = JP_DVD.clip_cut.std.AssumeFPS(fpsnum=24000, fpsden=1001)
    src_ncop, src_nced = JP_BD_NCOP.clip_cut, JP_BD_NCED.clip_cut
    src_ncop = src_ncop + src_ncop[-1] * 11
    src_nced = src_nced + src_nced[-1]
    src_03 = JP_BD_03.clip_cut

    src_ncop = flt.rekt(src_ncop)
    src_nced = flt.rekt(src_nced)
    src_03 = flt.rekt(src_03)

    # Fixing an animation error in the NCOP
    sqmask_ncop = lvf.mask.BoundingBox((419, 827), (1500, 68))
    masked_ncop = core.std.MaskedMerge(src_ncop, src_03, sqmask_ncop.get_mask(src_ncop))
    masked_ncop = lvf.rfs(src_ncop, masked_ncop, [(opstart+2064, opstart+2107)])

    op_mask = vdf.dcm(
        src_03, src_03[opstart:opstart+masked_ncop.num_frames-op_offset], masked_ncop[:-op_offset],
        start_frame=opstart, thr=85, prefilter=True) if opstart is not False \
        else get_y(core.std.BlankClip(src))
    op_mask = depth(core.resize.Bicubic(op_mask, 1296, 728).std.Crop(top=4, bottom=4), 16)

    # Stick credits ontop of NC because it looks way better
    masked_ncop = src_ncop.resize.Bicubic(chromaloc_in=1, chromaloc=0)
    cwarp_ncop = masked_ncop.warp.AWarpSharp2(thresh=88, blur=3, type=1, depth=6, planes=[1, 2])
    descale_ncop = lvf.kernels.Bicubic().descale(plane(depth(src_ncop, 16), 0), 1280, 720)
    chroma_down_ncop = core.resize.Bicubic(cwarp_ncop, 1280, 720, vs.YUV444P16)
    scaled_ncop = join([descale_ncop, plane(chroma_down_ncop, 1), plane(chroma_down_ncop, 2)])
    scaled_ncop = scaled_ncop.resize.Bicubic(1296, 728).std.Crop(top=4, bottom=4)
    downscale_03 = src_03.resize.Bicubic(1296, 728, vs.YUV444P16).std.Crop(top=4, bottom=4)
    merge_credits_03 = core.std.MaskedMerge(scaled_ncop, downscale_03, op_mask)

    for prop, val in PROPS_DVD:
        src = src.std.SetFrameProp(prop, intval=val)

    dvd_i444 = vdf.scale.to_444(depth(src, 32), src.width, src.height, join_planes=True)
    dvd_rgb = dvd_i444.resize.Bicubic(format=vs.RGB24, dither_type='error_diffusion', matrix_in=6)

    upscale = vsgan.run(dvd_rgb)
    conv = core.resize.Bicubic(upscale, format=vs.YUV444P16, matrix=1)
    scaled = depth(muf.SSIM_downsample(conv, 1296, 720), 16)

    splice_op = lvf.rfs(scaled, merge_credits_03, [(0, 203), (263, 1740), (1836, 2018)])

    # Splicing for the ED. Halves of the ED have visuals, others are credits
    masked_nced = src_nced.resize.Bicubic(chromaloc_in=1, chromaloc=0)
    cwarp_nced = masked_nced.warp.AWarpSharp2(thresh=88, blur=3, type=1, depth=6, planes=[1, 2])
    descale_nced = lvf.kernels.Bicubic().descale(plane(depth(src_nced, 16), 0), 1280, 720)
    chroma_down_nced = core.resize.Bicubic(cwarp_nced, 1280, 720, vs.YUV444P16)
    scaled_nced = join([descale_nced, plane(chroma_down_nced, 1), plane(chroma_down_nced, 2)])
    scaled_nced = scaled_nced.resize.Bicubic(1296, 728).std.Crop(top=4, bottom=4)

    ed_nc = scaled_nced
    ed_dvd = splice_op[31888:]

    sq_top = lvf.mask.BoundingBox((0, 0), (ed_nc.width, ed_nc.height/2)).get_mask(ed_nc)
    sq_left = lvf.mask.BoundingBox((0, 0), (ed_nc.width/2, ed_nc.height)).get_mask(ed_nc)
    sq_right = sq_left.std.Invert()

    mask_top = core.std.MaskedMerge(ed_dvd, ed_nc, sq_top)
    mask_left = core.std.MaskedMerge(ed_dvd, ed_nc, sq_left)
    mask_right = core.std.MaskedMerge(ed_dvd, ed_nc, sq_right)

    ed_splice = lvf.rfs(ed_dvd, mask_top, [(0, 1213), (1613, 1673), (1794, None)])
    ed_splice = lvf.rfs(ed_splice, mask_left, [(1390, 1503)])
    ed_splice = lvf.rfs(ed_splice, mask_right, [(1214, 1389), (1504, 1612), (1674, 1793)])

    splice_ed = insert_clip(splice_op, ed_splice, edstart)

    # Back to more regular filtering
    stab = haf.GSMC(splice_ed, radius=2, planes=[0])
    decs = vdf.noise.decsiz(stab, sigmaS=8, min_in=208 << 8, max_in=232 << 8)

    detail_mask = flt.detail_mask(decs, brz=(1800, 3500))
    deband = dbs.debanders.dumb3kdb(decs, threshold=32, grain=16)
    deband_masked = core.std.MaskedMerge(deband, decs, detail_mask)

    grain = vdf.noise.Graigasm(  # Mostly stolen from Varde tbh
        thrs=[x << 8 for x in (32, 80, 128, 176)],
        strengths=[(0.25, 0.0), (0.2, 0.0), (0.15, 0.0), (0.0, 0.0)],
        sizes=(1.2, 1.15, 1.05, 1),
        sharps=(65, 50, 40, 40),
        grainers=[
            vdf.noise.AddGrain(seed=69420, constant=True),
            vdf.noise.AddGrain(seed=69420, constant=False),
            vdf.noise.AddGrain(seed=69420, constant=False)
        ]).graining(deband_masked)

    return grain


if __name__ == '__main__':
    FILTERED = filterchain()
    enc.Encoder(JP_DVD, FILTERED).run(clean_up=True)  # type: ignore
elif __name__ == '__vapoursynth__':
    FILTERED = filterchain()
    if not isinstance(FILTERED, vs.VideoNode):
        raise ImportError(f"Input clip has multiple output nodes ({len(FILTERED)})! Please output just 1 clip")
    else:
        enc.dither_down(FILTERED).set_output(0)
else:
    JP_DVD.clip_cut.std.SetFrameProp('node', intval=0).set_output(0)
    FILTERED = filterchain()
    if not isinstance(FILTERED, vs.VideoNode):
        for i, clip_filtered in enumerate(FILTERED, start=1):
            clip_filtered.std.SetFrameProp('node', intval=i).set_output(i)
    else:
        FILTERED.std.SetFrameProp('node', intval=1).set_output(1)
