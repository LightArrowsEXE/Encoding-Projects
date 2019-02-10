import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import havsfunc as haf
import vsTAAmbk as taa
from nnedi3_rpow2 import nnedi3_rpow2
core = vs.core

src_jp = lvf.src(r"[BDMV][Katekyou Hitman REBORN!]\[家庭教師ヒットマンREBORN！][2006][TV][BDMV][Blu-ray BOX 1][JP][20170419]\REBORN_DISC9\BDMV\STREAM\00004.m2ts")
src_jp = src_jp[:2698] # for cutting audio

src_us = lvf.src(r"REBORN CS BD\REBORN SEASONS 1-4 BD\REBORN SEASONS 1-4 D2\BDMV\STREAM\00052.m2ts")
src_us = core.std.CropRel(src_us, 4, 4, 0, 0)
src_us = fvf.Depth(src_us, 16)

src_us = kgf.insert_clip(src_us, src_us[198], 197)
src_us = kgf.insert_clip(src_us, src_us[1305], 1306)
src_us = kgf.insert_clip(src_us, src_us[1448], 1449)
src_us = kgf.insert_clip(src_us, src_us[1450], 1451)
src_us = kgf.insert_clip(src_us, src_us[1465], 1464)
src_us = kgf.insert_clip(src_us, src_us[1735], 1734)
src_us = kgf.insert_clip(src_us, src_us[1795], 1796)

nn3 = core.nnedi3.nnedi3(src_us, field=0) # Fixing some leftover combing in transitions
src_us = fvf.rfs(src_us, nn3, mappings="[248 252] [1056 1062] [1108 1117] [1248 1260] [1984 1997]")

dehalo = haf.FineDehalo(src_us, rx=2, thmi=250, thma=255, thlimi=64, thlima=100)

scaled = nnedi3_rpow2(dehalo)
scaled = core.resize.Spline36(scaled, 960, 720, matrix_s='709')

denoised_a = lvf.denoise(scaled, h=0.8)
denoised_b = lvf.denoise(scaled, h=1.6, sigma=5)
denoised = fvf.rfs(denoised_a, denoised_b, mappings="[1262 1312] [1889 1933]")

sharp = haf.LSFmod(denoised, strength=140, soft=10, edgemode=1, Smethod=2, Lmode=2)

aa = taa.TAAmbk(sharp, aatype='Eedi3')

deband_a = core.f3kdb.Deband(aa, range=16, y=48, cb=40, cr=40, grainy=12, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(aa, range=18, y=64, cb=56, cr=56, grainy=12, grainc=0, output_depth=16)
deband = fvf.rfs(deband_a, deband_b, mappings="[1248 1260] [1916 1933]")

grain = kgf.adaptive_grain(deband, 1)

out = grain
final = fvf.Depth(out, 10)
final.set_output()