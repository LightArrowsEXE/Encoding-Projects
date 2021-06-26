import os
from typing import List

import adptvgrnMod as adp
import havsfunc as haf
import kagefunc as kgf
import lvsfunc as lvf
import vapoursynth as vs
import vardefunc as vdf
from awsmfunc import bbmod
from rekt import rektlvl
from vsutil import depth, join, split

core = vs.core

shader = r'FSRCNNX_x2_56-16-4-1.glsl'
if os.path.exists(shader) is False:
    hookpath = r"mpv/shaders/FSRCNNX_x2_56-16-4-1.glsl"
    shader = os.path.join(os.getenv("APPDATA"), hookpath)


def morpho_mask_simple(clip, radius=3, **mode):
    from vsutil import plane

    clip_y = plane(clip, 0)
    refa = haf.mt_inpand_multi(haf.mt_expand_multi(clip_y, sw=radius, sh=radius, **mode), sw=radius, sh=radius, **mode)
    refb = haf.mt_expand_multi(haf.mt_inpand_multi(clip_y, sw=radius, sh=radius, **mode), sw=radius, sh=radius, **mode)
    return core.std.Expr([clip_y, refa, refb], 'x y - abs x z - abs max')


def detail_mask(clip: vs.VideoNode,
                sigma: float = 1.0, rxsigma: List[int] = [50, 200, 350],
                pf: bool = False, pf_sigma: float = 1.0,
                rad: int = 3, brz: int = [2500, 4500], rg_mode: int = 17,
                ) -> vs.VideoNode:
    """
    A detail mask aimed at preserving as much detail as possible
    within darker areas, even if it contains mostly noise.
    """
    import kagefunc as kgf
    from vsutil import depth, get_depth, get_y, iterate

    bits = get_depth(clip)

    if bits != 16:
        clip = depth(clip, 16)

    clip_y = get_y(clip)
    pf = core.bilateral.Gaussian(clip_y, sigma=pf_sigma) if pf else clip_y
    ret = core.retinex.MSRCP(pf, sigma=rxsigma, upper_thr=0.005)

    blur_ret = core.bilateral.Gaussian(ret, sigma=sigma)
    blur_ret_diff = core.std.Expr([blur_ret, ret], "x y -")
    blur_ret_dfl = core.std.Deflate(blur_ret_diff)
    blur_ret_ifl = iterate(blur_ret_dfl, core.std.Inflate, 4)
    blur_ret_brz = core.std.Binarize(blur_ret_ifl, brz[0])
    blur_ret_brz = core.morpho.Close(blur_ret_brz, size=8)

    kirsch = kgf.kirsch(clip_y).std.Binarize(brz[1])
    kirsch_ifl = core.std.Deflate(kirsch).std.Inflate()
    kirsch_brz = core.std.Binarize(kirsch_ifl, brz[1])
    kirsch_brz = core.morpho.Close(kirsch_brz, size=4)

    morpho_mask = morpho_mask_simple(clip, radius=rad)

    merged = core.std.Expr([blur_ret_brz, kirsch_brz, morpho_mask], "x y + z +")
    rm_grain = core.rgvs.RemoveGrain(merged, rg_mode)
    return rm_grain if bits == 16 else depth(rm_grain, bits)


# first frame of OP, ED
opstart = False
edstart = 0

# Scenefiltering OP/ED
op_no_edgefix_ranges = [(opstart+1338, opstart+1418)] if opstart is not False else []
op_stronger_deband_ranges = [(opstart+40, opstart+127), (opstart+1130, opstart+1239)] if opstart is not False else []
op_stronger_grain_ranges = [(opstart+40, opstart+127), (opstart+1130, opstart+1239)] if opstart is not False else []

# Scenefiltering regular
no_edgefix_ranges = [] + op_no_edgefix_ranges
stronger_deband_ranges = [] + op_stronger_deband_ranges
stronger_grain_ranges = [] + op_stronger_grain_ranges


src = lvf.src(r"[BDMV] Ore-tachi ni Tsubasa wa Nai/[BDMV] [110622] 俺たちに翼はない Vol.1/ORETSUBA_01/BDMV/STREAM/00004.m2ts")[:-24] # noqa


# Edgefixing
rkt = rektlvl(src, 2, 1, prot_val=False)
rkt = rektlvl(rkt, 1, -4, prot_val=[15, 230])
rkt = rektlvl(rkt, 0, 1, prot_val=[15, 230])

rkt = rektlvl(rkt, src.height-3, 1, prot_val=False)
rkt = rektlvl(rkt, src.height-2, -4, prot_val=[15, 230])
rkt = rektlvl(rkt, src.height-1, 1, prot_val=[15, 230])

rkt = rektlvl(rkt, 0, 1, type='column', prot_val=False)
rkt = rektlvl(rkt, 1, -4, type='column', prot_val=[15, 230])
rkt = rektlvl(rkt, 2, 1, type='column', prot_val=[15, 230])

rkt = rektlvl(rkt, src.width-3, 1, type='column', prot_val=False)
rkt = rektlvl(rkt, src.width-2, -4, type='column', prot_val=[15, 230])
rkt = rektlvl(rkt, src.width-1, 1, type='column', prot_val=[15, 230])

ef = bbmod(rkt, left=3, top=3, bottom=3, right=3, thresh=8, y=True, u=False, v=False)
ef = depth(ef, 32)

# Descaling
b, c = vdf.misc.get_bicubic_params('Robidoux Sharp')

planes = split(ef)
descale = core.descale.Debicubic(planes[0], 1280, 720, b=b, c=c)

rescaled_fsrcnx = vdf.scale.fsrcnnx_upscale(descale, shader_file=shader)
rescaled_nnedi3 = vdf.scale.nnedi3_upscale(descale, pscrn=1).resize.Bicubic(ef.width, ef.height)
rescaled = core.std.Merge(rescaled_fsrcnx, rescaled_nnedi3)

scaled = join([rescaled, planes[1], planes[2]])
scaled = depth(scaled, 16)

# Try to limit oversharpening
ef16 = depth(ef, 16)

halo_mask = lvf.mask.halo_mask(scaled, rad=3, brz=0.2)
blur_ref = core.bilateral.Bilateral(scaled, sigmaS=0.75, sigmaR=4/255)
blur = core.bilateral.Bilateral(scaled, sigmaS=1, sigmaR=4/255, ref=blur_ref)
dehalo = core.std.MaskedMerge(scaled, blur, halo_mask)


den_ref = haf.SMDegrain(dehalo, thSAD=350, thSADC=350)
denoise = lvf.denoise.bm3d(dehalo, sigma=1.25, radius=2, ref=den_ref)
denoise = vdf.noise.decsiz(denoise, sigmaS=8, min_in=224 << 8, max_in=240 << 8)


deb_mask = detail_mask(dehalo)
deband_wk = vdf.deband.dumb3kdb(denoise, radius=17, threshold=32)
deband_str = vdf.deband.dumb3kdb(deband_wk, radius=13, threshold=32)
deband = lvf.rfs(deband_wk, deband_str, stronger_deband_ranges)
deband_masked = core.std.MaskedMerge(deband, dehalo, deb_mask)


grain_wk = kgf.adaptive_grain(deband, 0.25, luma_scaling=6)
grain_str = adp.adptvgrnMod(deband, strength=0.25, size=1.6, sharp=80, grain_chroma=False, luma_scaling=4, seed=42069)
grain = lvf.rfs(grain_wk, grain_str, stronger_grain_ranges)


out = grain
final = depth(out, 10)
final.set_output(0)


if __name__ == '__vapoursynth__':
    import ntpath
    import os

    import kagefunc as kgf

    def keyframes(clip: vs.VideoNode, kf_path: str):
        if not os.path.isdir("keyframes"):
            os.makedirs("keyframes")
        kgf.generate_keyframes(clip, out_path=kf_path, header=False)

    kf_path = f"keyframes/{ntpath.basename(__file__)[:-4]}_keyframes.txt"
    if not os.path.isfile(kf_path):
        keyframes(src, kf_path)
