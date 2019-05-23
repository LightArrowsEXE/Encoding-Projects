import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import havsfunc as haf
import vsTAAmbk as taa
from nnedi3_rpow2 import nnedi3_rpow2
import adjust
core = vs.core

src_jp = lvf.src(r"[BDMV][Katekyou Hitman REBORN!]\[家庭教師ヒットマンREBORN！][2006][TV][BDMV][Blu-ray BOX 2][JP][20170517]\REBORN2_DISC9\BDMV\STREAM\00008.m2ts")
src_jp = src_jp[:2698] # for cutting audio

src_us = lvf.src(r"REBORN CS BD\REBORN SEASONS 5-9 BD\REBORN SEASONS 5-9 D1\BDMV\STREAM\00051.m2ts")
src_us = core.std.CropRel(src_us, 4, 4, 0, 0)
src_us = fvf.Depth(src_us, 16)

src_us = kgf.insert_clip(src_us, src_us[1539:1579], 1536)
src_us = kgf.insert_clip(src_us, src_us[1578]*2, 1575)
src_us = kgf.insert_clip(src_us, src_us[1579]*2, 1576)
src_us = kgf.insert_clip(src_us, src_us[1580]*2, 1578)
src_us = kgf.insert_clip(src_us, src_us[1581:1598], 1580)
src_us = kgf.insert_clip(src_us, src_us[1599], 1598)

mask = kgf.retinex_edgemask(src_us).std.Binarize()
blur = kgf.iterate(src_us, core.std.BoxBlur, 3)
blur = core.std.MaskedMerge(src_us, blur, mask)
src_us = fvf.rfs(src_us, blur, mappings="[420 423]")

nn3 = core.nnedi3.nnedi3(src_us, field=0)
w2x = fvf.Depth(nn3, 32) # If throwing away fields destroys too much detail, just reinvent new detail! ヽ( ﾟヮ・)ノ
w2x = fvf.Depth(core.resize.Spline36(core.w2xc.Waifu2x(w2x, noise=1, scale=2, gpu=2), 712, 480), 16)
src_us = fvf.rfs(src_us, w2x, mappings="[76 80] [420 422] [1016 1029] [1624 1643] [1931 1942]")

dehalo = haf.FineDehalo(src_us, rx=2, thmi=250, thma=255, thlimi=64, thlima=100)

scaled = nnedi3_rpow2(dehalo)
scaled = core.resize.Spline36(scaled, 1280, 720, matrix_in_s='709', format=vs.YUV420P16)

denoised = lvf.denoise(scaled, h=0.8)

sharp = haf.LSFmod(denoised, strength=140, soft=10, edgemode=1, Smethod=2, Lmode=2)

aa = taa.TAAmbk(sharp, aatype='Eedi3')

deband = core.f3kdb.Deband(aa, range=16, y=48, cb=40, cr=40, grainy=12, grainc=0, output_depth=16)

grain_a = kgf.adaptive_grain(deband, 0.1)
grain_b = kgf.adaptive_grain(deband, 1)
grain_c = kgf.adaptive_grain(deband, 2)
grain = fvf.rfs(grain_a, grain_b, mappings="[0 296] [1209 1239] [1304 1417] [1465 1511] [2003 2065]")
grain = fvf.rfs(grain, grain_c, mappings="[1091 1208]")

out = grain
final = fvf.Depth(out, 10)
final.set_output()