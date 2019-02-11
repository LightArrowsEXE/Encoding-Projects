import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import havsfunc as haf
import vsTAAmbk as taa
from nnedi3_rpow2 import nnedi3_rpow2
core = vs.core

src_jp = lvf.src(r"[BDMV][Katekyou Hitman REBORN!]\[家庭教師ヒットマンREBORN！][2006][TV][BDMV][Blu-ray BOX 2][JP][20170517]\REBORN2_DISC9\BDMV\STREAM\00005.m2ts")
src_jp = src_jp[4:2700] # for cutting audio

src_us = lvf.src(r"REBORN CS BD\REBORN SEASONS 5-9 BD\REBORN SEASONS 5-9 D1\BDMV\STREAM\00050.m2ts")
src_us = core.std.CropRel(src_us, 4, 4, 0, 0)
src_us = src_us[2:]
src_us = fvf.Depth(src_us, 16)

src_us = kgf.insert_clip(src_us, src_us[93], 92)
src_us = kgf.insert_clip(src_us, src_us[97], 96)
src_us = kgf.insert_clip(src_us, src_us[101], 100)
src_us = kgf.insert_clip(src_us, src_us[105], 104)
src_us = kgf.insert_clip(src_us, src_us[873], 875)

nn3 = core.nnedi3.nnedi3(src_us, field=0)
w2x = fvf.Depth(nn3, 32) # If throwing away fields destroys too much detail, just reinvent new detail! ヽ( ﾟヮ・)ノ
w2x = fvf.Depth(core.resize.Spline36(core.w2xc.Waifu2x(w2x, noise=1, scale=2, gpu=2), 712, 480), 16)
#src_us = fvf.rfs(src_us, w2x, mappings="[89 114] [245 252] [468 471] [825 833] [1291 1309]")
src_us = core.std.AssumeFPS(src_us, fpsnum=24000, fpsden=1001)

dehalo = haf.FineDehalo(src_us, rx=2, thmi=250, thma=255, thlimi=64, thlima=100)

scaled = nnedi3_rpow2(dehalo)
scaled = core.resize.Spline36(scaled, 1280, 720, matrix_s='709')

denoised = lvf.denoise(scaled, h=1.6)
denoised = fvf.rfs(denoised, scaled, mappings="[1547 1576]")

sharp = haf.LSFmod(denoised, strength=140, soft=10, edgemode=1, Smethod=2, Lmode=2)

darken = haf.FastLineDarkenMOD(sharp, strength=48)
darken = fvf.rfs(sharp, darken, mappings="[468 471]")

aa_a = taa.TAAmbk(darken, aatype='Eedi3')
aa_b = taa.TAAmbk(darken, aatype=4)
aa = fvf.rfs(aa_a, aa_b, mappings="[89 124]")

deband_a = core.f3kdb.Deband(aa, range=16, y=48, cb=40, cr=40, grainy=12, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(aa, range=5, y=96, cb=88, cr=88, grainy=0, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(deband_b, range=21, y=56, cb=48, cr=48, grainy=24, grainc=0, output_depth=16)
deband_c = core.f3kdb.Deband(aa, range=21, y=72, cb=64, cr=64, grainy=0, grainc=0, output_depth=16)
deband = fvf.rfs(deband_a, deband_b, mappings="[468 471]")
deband = fvf.rfs(deband, deband_c, mappings="[210 425] [556 585] [678 824] [1221 1290] [1380 1514] [1856 1922]")

grain_a = kgf.adaptive_grain(deband, 0.1)
grain_b = kgf.adaptive_grain(deband, 1)
grain_c = kgf.adaptive_grain(deband, 2)
grain = fvf.rfs(grain_a, grain_b, mappings="[250 279] [556 585] [1203 1220] [1380 1514] [1856 1922]")
grain = fvf.rfs(grain, grain_c, mappings="[210 249] [426 471] [678 824] [1577 1693]")

out = grain
final = fvf.Depth(out, 10)
final.set_output()