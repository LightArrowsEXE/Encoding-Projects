import os

import fvsfunc as fvf
import G41Fun as g41
import havsfunc as haf
import kagefunc as kgf
import lvsfunc as lvf
import mvsfunc as mvf
import xvs
from finedehalo import fine_dehalo
from vsutil import depth, join, plane

import vapoursynth as vs

core = vs.core
core.max_cache_size = 1024 * 4
core.num_threads = 12


shader = 'FSRCNNX_x2_56-16-4-1.glsl'
if os.path.exists(shader) is False:
    hookpath = r"mpv\shaders\FSRCNNX_x2_56-16-4-1.glsl"
    shader = os.path.join(os.getenv("APPDATA"), hookpath)


# Common args
deband_a_args = dict(iterations=2, threshold=4, radius=16)
deband_b_args = dict(iterations=4, threshold=8, radius=12)

src = lvf.src("src/Fate Grand Order -First Order- Fate Project (BS11).dgi")
dec = lvf.deinterlace.decomb(src, TFF=True)
dec = dec[113503:115443] + dec[121382:123205] \
    + dec[136688:137764] + dec[144624:146134] \
    + dec[160069:162322] + dec[162321] * 30
dec = depth(dec, 16)

cs = haf.FixChromaBleedingMod(dec, cx=-0.65, cy=0, thr=100, strength=1, blur=True)

delogo = core.delogohd.DelogoHD(cs, 'BS11v2a 1920x1080.lgd', top=0, cutoff=100)
delogo_smooth = haf.logoNR(delogo, cs, l=1600, t=30, r=60, b=700, h=30)
delogo_smooth = lvf.rfs(delogo_smooth, cs, [(3763, 4272)])

debl = fvf.AutoDeblock(delogo_smooth)

nn3_args = dict(nsize=4, nns=4, qual=2, pscrn=1)

nn3 = debl.std.Transpose().nnedi3.nnedi3(0, True, **nn3_args) \
        .std.Transpose().nnedi3.nnedi3(0, True, **nn3_args)
nn3 = core.resize.Spline36(nn3, src_top=.5, src_left=.5)
nn3 = core.resize.Bicubic(nn3, dec.width, dec.height)

sharp = g41.psharpen(nn3)

l_mask = g41.EdgeDetect(debl, mode="FDOG", multi=1)
sharp = join([sharp, plane(debl, 1), plane(debl, 2)])
merge = core.std.MaskedMerge(debl, sharp, l_mask)
merge = lvf.rfs(merge, nn3, [(3763, 4272)])

cwarp = core.std.MaskedMerge(
    xvs.WarpFixChromaBlend(merge, depth=8),
    merge, l_mask)
cwarp = core.rgvs.Repair(cwarp, merge, 13)

dering = haf.EdgeCleaner(cwarp, strength=8, rmode=13, hot=True)
dehalo = fine_dehalo(dering, rx=2.4, ry=2.2, darkstr=0, brightstr=1)

denoise = mvf.BM3D(dehalo, sigma=[1.6, 1.2], profile1='lc')

detail_mask = lvf.denoise.detail_mask(denoise, rad=2, radc=1, brz_a=0.025, brz_b=0.02)
deband_a = join([
    core.placebo.Deband(plane(denoise, 0), grain=4, **deband_a_args),
    core.placebo.Deband(plane(denoise, 1), grain=0, **deband_a_args),
    core.placebo.Deband(plane(denoise, 2), grain=0, **deband_a_args)
])
deband_a = core.std.MaskedMerge(deband_a, denoise, detail_mask)
deband_b = join([
    core.placebo.Deband(plane(denoise, 0), grain=4, **deband_b_args),
    core.placebo.Deband(plane(denoise, 1), grain=0, **deband_b_args),
    core.placebo.Deband(plane(denoise, 2), grain=0, **deband_b_args)
])
deband = lvf.rfs(
    deband_a, deband_b,
    [(7415, 8520)]
)

grain = lvf.rfs(
    kgf.adaptive_grain(deband, 0.2, luma_scaling=4),
    kgf.adaptive_grain(deband, 4.0, luma_scaling=4, static=False),
    [(3763, 3935), (4017, 4057)])
grain = lvf.rfs(
    grain, kgf.adaptive_grain(deband, 1.4, luma_scaling=4),
    [(3936, 4016), (4058, 4271)]
)


out = grain
final = depth(out, 10)
final.set_output()
