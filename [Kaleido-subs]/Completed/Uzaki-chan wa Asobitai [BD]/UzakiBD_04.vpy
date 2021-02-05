"""
Lazy script. Probably still gonna be way better than most releases tho lmfao
"""
import havsfunc as haf
import kagefunc as kgf
import lvsfunc as lvf
import vapoursynth as vs
import vardefunc as vdf
from vsutil import depth, get_y, iterate, join, plane

core = vs.core


def placebo_debander(clip: vs.VideoNode, grain: int = 4, **deband_args) -> vs.VideoNode:
    return join([  # Still not sure why splitting it up into planes is faster, but hey!
        core.placebo.Deband(plane(clip, 0), grain=grain, **deband_args),
        core.placebo.Deband(plane(clip, 1), grain=0, **deband_args),
        core.placebo.Deband(plane(clip, 2), grain=0, **deband_args)
    ])


# Common args
deband_args = dict(grain=2, iterations=2, threshold=3, radius=14)

# Second cut, first frame for both
opstart = 1302
edstart = 31981

op_offset = 2
ed_offset = 1

# Scenefiltering
op_replace = [(24, 29), (58, 64), (92, 97), (127, 133), (151, 157), (176, 181), (2008, 2019)]


src = lvf.src(r"BDMV/[BDMV] Uzaki-chan Wants to Hang Out! Volume 1/UZAKICHAN_WA_ASOBITAI_01/BDMV/STREAM/00012.m2ts")[24:-24]
bl, src_c = core.std.BlankClip(src), src

if opstart is not False:
    src_NCOP = lvf.src(r"BDMV/[BDMV] Uzaki-chan Wants to Hang Out! Volume 1/UZAKICHAN_WA_ASOBITAI_01/BDMV/STREAM/00017.m2ts")[24:-24]
    op_scomp = lvf.scomp(src[opstart-30:opstart-30+src_NCOP.num_frames-1-op_offset]+bl[0], src_NCOP+bl[0], make_diff=True)

    # Replace grain areas, since they look *slightly* better in the NCOP
    for a, b in op_replace:
        src = kgf.insert_clip(src, src_NCOP[a:b+1], opstart-30+a)

    # Replace jp in OP
    sqmask = kgf.squaremask(src, 1920, 146, 0, 934)
    mask_jp = core.std.MaskedMerge(src, bl[:opstart-30]+src_NCOP[:-op_offset], sqmask)
    src = lvf.rfs(src, mask_jp[:-op_offset], [(opstart-30, opstart-30+src_NCOP.num_frames-45-op_offset)])

if edstart is not False:
    src_NCED = lvf.src(r"BDMV/[BDMV] Uzaki-chan Wants to Hang Out! Volume 2/UZAKICHAN_WA_ASOBITAI_02/BDMV/STREAM/00018.m2ts")[24:-24]
    ed_scomp = lvf.scomp(src[edstart-212:edstart-212+src_NCED.num_frames-1]+bl[0], src_NCED[:-ed_offset]+src[1000], make_diff=True)

    # Replace jp in ED
    sqmask = kgf.squaremask(src, 1920, 146, 0, 934)
    mask_jp = core.std.MaskedMerge(src, bl[:edstart-212]+src_NCED[:-op_offset], sqmask)
    src = lvf.rfs(src, mask_jp[:-ed_offset], [(edstart-212, edstart-212+src_NCED.num_frames-78-ed_offset)])


# Masking credits
op_mask = vdf.diff_creditless_mask(src, src[opstart-30:opstart-30+src_NCOP.num_frames-1-op_offset],
                                   src_NCOP[:-op_offset], opstart-30, opstart-30+src_NCOP.num_frames-1) \
                                   if opstart is not False else get_y(core.std.BlankClip(src))
ed_mask = vdf.diff_creditless_mask(src, src[edstart-212:edstart+src_NCED.num_frames-2-ed_offset],
                                   src_NCED[:-ed_offset], edstart-212, edstart-212+src_NCED.num_frames-1) \
                                   if edstart is not False else get_y(core.std.BlankClip(src))
credit_mask = core.std.Expr([op_mask, ed_mask], expr='x y +')
credit_mask = iterate(credit_mask, core.std.Maximum, 3)
credit_mask = depth(credit_mask, 16).std.Binarize()

src = depth(src, 16)

denoise = haf.SMDegrain(src, thSAD=80)
aa = core.znedi3.nnedi3(denoise, field=0, dh=True, nsize=4, nns=4, qual=2, pscrn=2)
aa = core.resize.Bicubic(aa, src.width, src.height, src_top=0.5)
ec = haf.EdgeCleaner(aa, strength=3, rmode=13, hot=True)

merge = core.std.MaskedMerge(ec, src, get_y(credit_mask))

deband_mask = lvf.mask.detail_mask(merge, sigma=0.8, brz_a=0.008, brz_b=0.015)
deband = placebo_debander(merge, **deband_args)
deband = core.std.MaskedMerge(deband, merge, deband_mask)

grain = kgf.adaptive_grain(deband, 0.1, luma_scaling=4)


out = grain
final = depth(out, 10)
final.set_output()


if __name__ == '__vapoursynth__':
    import ntpath
    import os

    def keyframes(clip: vs.VideoNode, kf_path: str):
        if not os.path.isdir("keyframes"):
            os.makedirs("keyframes")
        kgf.generate_keyframes(clip, out_path=kf_path, header=False)

    kf_path = f"keyframes/{ntpath.basename(__file__)[:-4]}_keyframes.txt"
    if not os.path.isfile(kf_path):
        keyframes(src, kf_path)
