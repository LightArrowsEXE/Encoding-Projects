import havsfunc as haf
import kagefunc as kgf
import lvsfunc as lvf
import mvsfunc as mvf
from vsTAAmbk import *
from vsutil import *

import vapoursynth as vs

core = vs.core


opstart = 2374
edstart = 32127


src = lvf.src(r'BDMV/[BDMV][191204][Machikado Mazoku][Vol.3]/MACHIKADO_MAZOKU_3/BDMV/STREAM/00006.m2ts')[:-24]
src = depth(src, 32)


scaled = lvf.scale.descale(src, height=[958, 980], kernel=lvf.kernels.Bicubic(b = 0,c = 1 / 2), threshold=0.02)
scaled = depth(scaled, 16)


l_mask = kgf.retinex_edgemask(src, 1).std.Binarize().std.Inflate().std.Maximum()
ref = core.knlm.KNLMeansCL(src, d=2, h=4)
denoise = mvf.BM3D(src, sigma=[1.25, 1], depth=16, ref=ref, profile1='fast')
csharp = haf.ContraSharpening(denoise, src)
masked = core.std.MaskedMerge(csharp, src, l_mask)

aa = lvf.rfs(TAAmbk(masked, aatype='Nnedi3'),
             lvf.upscaled_sraa(masked),
             [(opstart+57, opstart+102), (opstart+124, opstart+180),
              (opstart+1713, opstart+1749), (edstart+1965, edstart+2159)])

deband = core.f3kdb.Deband(aa, range=18, output_depth=16, preset="medium/nograin")
grain = kgf.adaptive_grain(deband, 0.15, luma_scaling=16)


out = grain
final = depth(out, 10)
final.set_output()
