import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import havsfunc as haf
import vsTAAmbk as taa
from nnedi3_rpow2 import nnedi3_rpow2
core = vs.core

src_jp = lvf.src(r"[BDMV][Katekyou Hitman REBORN!]\[家庭教師ヒットマンREBORN！][2006][TV][BDMV][Blu-ray BOX 3][JP][20170621]\REBORN3_DISC8\BDMV\STREAM\00005.m2ts")
src_jp = src_jp[16:2698] # for cutting audio

src_us = lvf.src(r"REBORN CS BD\REBORN SEASONS 5-9 BD\REBORN SEASONS 5-9 D1\BDMV\STREAM\00060.m2ts")
src_us = core.std.CropRel(src_us, 4, 4, 0, 0)
src_us = core.std.AssumeFPS(src_us, fpsnum=24000, fpsden=1001)
src_us = fvf.Depth(src_us, 16)

nn3 = core.nnedi3.nnedi3(src_us, field=0)
w2x = fvf.Depth(nn3, 32) # If throwing away fields destroys too much detail, just reinvent new detail! ヽ( ﾟヮ・)ノ
w2x = fvf.Depth(core.resize.Spline36(core.w2xc.Waifu2x(w2x, noise=1, scale=2, gpu=2), 712, 480), 16)
src_us = fvf.rfs(src_us, w2x, mappings="[299 323] [349 359] [390 400] [438 472] [597 607] [738 748] [886 896] [1030 1040]")

dehalo = haf.FineDehalo(src_us, rx=2, thmi=250, thma=255, thlimi=64, thlima=100)

scaled = nnedi3_rpow2(dehalo)
scaled = core.resize.Spline36(scaled, 1280, 720, matrix_s='709')

denoised = lvf.denoise(scaled, h=0.8)

sharp = haf.LSFmod(denoised, strength=140, soft=10, edgemode=1, Smethod=2, Lmode=2)

aa = taa.TAAmbk(sharp, aatype='Eedi3')

deband_a = core.f3kdb.Deband(aa, range=16, y=48, cb=40, cr=40, grainy=12, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(aa, range=18, y=56, cb=48, cr=48, grainy=12, grainc=0, output_depth=16)
deband = fvf.rfs(deband_a, deband_b, mappings="[1371 1514] [1582 1803]")

grain = kgf.adaptive_grain(deband, 1)
grain = fvf.rfs(deband, grain, mappings="[1371 1803]")

out = grain
final = fvf.Depth(out, 10)
final.set_output()