import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import havsfunc as haf
import vsTAAmbk as taa
from nnedi3_rpow2 import nnedi3_rpow2
core = vs.core

src_jp = lvf.src(r"[BDMV][Katekyou Hitman REBORN!]\[家庭教師ヒットマンREBORN！][2006][TV][BDMV][Blu-ray BOX 3][JP][20170621]\REBORN3_DISC8\BDMV\STREAM\00002.m2ts")
src_jp = src_jp[:2698] # for cutting audio

src_us = lvf.src(r"REBORN CS BD\REBORN SEASONS 5-9 BD\REBORN SEASONS 5-9 D1\BDMV\STREAM\00052.m2ts")
src_us = core.std.CropRel(src_us, 4, 4, 0, 0)
src_us = fvf.Depth(src_us, 16)

src_us = kgf.insert_clip(src_us, src_us[1795], 1794)

nn3 = core.nnedi3.nnedi3(src_us, field=0)
w2x = fvf.Depth(nn3, 32) # If throwing away fields destroys too much detail, just reinvent new detail! ヽ( ﾟヮ・)ノ
w2x = fvf.Depth(core.resize.Spline36(core.w2xc.Waifu2x(w2x, noise=1, scale=2, gpu=2), 712, 480), 16)
#src_us = fvf.rfs(src_us, w2x, mappings="[0 14] [507 511] [525 530] [560 565] [617 622] [1535 1542] [1850 1860] [1897 1908]")

dehalo = haf.FineDehalo(src_us, rx=2, thmi=250, thma=255, thlimi=64, thlima=100)

scaled = nnedi3_rpow2(dehalo)
scaled = core.resize.Spline36(scaled, 1280, 720, matrix_s='709')

denoised = lvf.denoise(scaled, h=1.6)

sharp = haf.LSFmod(denoised, strength=140, soft=10, edgemode=1, Smethod=2, Lmode=2)

darken = haf.FastLineDarkenMOD(sharp, strength=48)
darken = fvf.rfs(sharp, darken, mappings="[331 453]")

aa = taa.TAAmbk(darken, aatype='Eedi3')

deband = core.f3kdb.Deband(aa, range=16, y=48, cb=40, cr=40, grainy=12, grainc=0, output_depth=16)

grain = kgf.adaptive_grain(deband, 0.1)

out = grain
final = fvf.Depth(out, 10)
scaled.set_output()