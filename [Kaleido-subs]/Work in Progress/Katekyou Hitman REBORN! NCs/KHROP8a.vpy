import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import havsfunc as haf
import vsTAAmbk as taa
from nnedi3_rpow2 import nnedi3_rpow2
core = vs.core

src_jp = lvf.src(r"[BDMV][Katekyou Hitman REBORN!]\[家庭教師ヒットマンREBORN！][2006][TV][BDMV][Blu-ray BOX 3][JP][20170621]\REBORN3_DISC8\BDMV\STREAM\00003.m2ts")
src_jp = src_jp[:2698] # for cutting audio

src_us = lvf.src(r"REBORN CS BD\REBORN SEASONS 5-9 BD\REBORN SEASONS 5-9 D1\BDMV\STREAM\00053.m2ts")
src_us = core.std.AssumeFPS(src_us, fpsnum=24000, fpsden=1001)
src_us = core.std.CropRel(src_us, 4, 4, 0, 0)
src_us = fvf.Depth(src_us, 16)

src_us = kgf.insert_clip(src_us, src_us[702], 703)
src_us = kgf.insert_clip(src_us, src_us[778], 779)
src_us = kgf.insert_clip(src_us, src_us[878], 879)

dehalo = haf.FineDehalo(src_us, rx=2, thmi=250, thma=255, thlimi=64, thlima=100)

scaled = nnedi3_rpow2(dehalo)
scaled = core.resize.Spline36(scaled, 1280, 720, matrix_s='709')

denoised = lvf.denoise(scaled, h=1.6)

sharp = haf.LSFmod(denoised, strength=140, soft=10, edgemode=1, Smethod=2, Lmode=2)

aa = taa.TAAmbk(sharp, aatype='Eedi3')

deband = core.f3kdb.Deband(aa, range=16, y=48, cb=40, cr=40, grainy=12, grainc=0, output_depth=16)

grain_a = kgf.adaptive_grain(deband, 0.1)
grain_b = kgf.adaptive_grain(deband, 0.8)
grain = fvf.rfs(grain_a, grain_b, mappings="[0 166] [198 231] [263 451]")

out = grain
final = fvf.Depth(out, 10)
final.set_output()