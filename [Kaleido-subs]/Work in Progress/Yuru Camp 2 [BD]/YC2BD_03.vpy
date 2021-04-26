from typing import List, Tuple

import adptvgrnMod as adp
import G41Fun as gf
import havsfunc as haf
import kagefunc as kgf
import lvsfunc as lvf
import vapoursynth as vs
import vardefunc as vdf
from finedehalo import fine_dehalo
from vsutil import depth, get_depth, get_y, iterate

core = vs.core


def get_linemask(clip: vs.VideoNode, brz: int = 4500,
                 rxsigma: List[int] = [50, 200, 350]
                 ) -> vs.VideoNode:
    clip_y = get_y(clip)
    ret = core.retinex.MSRCP(clip_y, sigma=rxsigma, upper_thr=0.005)
    return kgf.kirsch(ret).std.Binarize(brz)


def detail_mask(clip: vs.VideoNode,
                sigma: float = 1.0, rxsigma: List[int] = [50, 200, 350],
                pf: bool = False, pf_sigma: float = 1.0,
                brz: Tuple[int] = (2500, 4500), rg_mode: int = 17,
                ) -> vs.VideoNode:
    """
    A detail mask aimed at preserving as much detail as possible
    within darker areas, even if it contains mostly noise.
    """
    bits = get_depth(clip)

    if bits != 16:
        clip = depth(clip, 16)

    clip_y = get_y(clip)
    pf = core.bilateral.Gaussian(clip_y, sigma=pf_sigma) if pf else clip_y
    ret = core.retinex.MSRCP(pf, sigma=rxsigma, upper_thr=0.005)

    blur_ret = core.bilateral.Gaussian(ret, sigma=sigma)
    blur_ret_diff = core.std.Expr([blur_ret, ret], "x y -").std.Binarize(brz[0])

    kirsch = kgf.kirsch(clip_y).std.Binarize(brz[1])
    merged = core.std.Expr([blur_ret_diff, kirsch], "x y +")
    rm_grain = core.rgvs.RemoveGrain(merged, rg_mode)
    return rm_grain if bits == 16 else depth(rm_grain, bits)


# Common args
scale_args = dict(height=[842, 846], threshold=0.00085, kernel=lvf.kernels.Bicubic())


src = lvf.src(r"BDMV/[BDMV][210324][Yuru Camp Season 2][Vol.1]/BD/BDMV/STREAM/00006.m2ts")[:-49]
src = depth(src, 32)


l_mask1 = gf.EdgeDetect(src, mode='frei-chen')
descale = lvf.scale.descale(src, **scale_args)
scaled = core.std.MaskedMerge(src, descale, l_mask1)
scaled_rep = core.rgsf.Repair(scaled, src, 17)

l_mask2 = get_linemask(depth(scaled_rep, 16))
aa_wk = lvf.aa.nnedi3(scaled_rep)
aa_st = lvf.sraa(scaled_rep, rfactor=1.6, downscaler=lvf.kernels.Bicubic().scale, rep=17)
aa = lvf.aa.clamp_aa(scaled_rep, aa_wk, aa_st).rgsf.Repair(scaled, 17)
down = depth(aa, 16)
mask_aa = core.std.MaskedMerge(depth(src, 16), down, l_mask2)


src_y = depth(get_y(src), 8)
bright_mask = core.std.Expr(src_y, "x 230 > x 255 < and 255 0 ?")
bright_mask_close = core.morpho.Close(bright_mask, size=8)
bright_mask_grow = iterate(bright_mask_close, core.std.Inflate, 4)
credit_mask = depth(bright_mask_grow, 16).resize.Bicubic(src_top=1, src_left=1)


mask_credits = core.std.MaskedMerge(mask_aa, depth(src, 16), credit_mask)

dehalo = fine_dehalo(mask_credits, rx=2, darkstr=0, brightstr=0.7)
cdenoise = haf.SMDegrain(dehalo, thSAD=150, plane=3)
denoise = vdf.decsiz(cdenoise, sigmaS=4, min_in=208 << 8, max_in=232 << 8)

deb_mask = detail_mask(denoise)
deband = vdf.dumb3kdb(denoise, radius=17, threshold=24, grain=12)
deband = core.std.MaskedMerge(deband, denoise, deb_mask)

grain = adp.adptvgrnMod(deband, strength=0.2, size=1.2, grain_chroma=False, luma_scaling=4)


out = grain
final = depth(out, 10)
final.set_output(0)


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
