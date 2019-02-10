import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import havsfunc as haf
import vsTAAmbk as taa
from nnedi3_rpow2 import nnedi3_rpow2
core = vs.core

src_jp = lvf.src(r"[BDMV][Katekyou Hitman REBORN!]\[家庭教師ヒットマンREBORN！][2006][TV][BDMV][Blu-ray BOX 2][JP][20170517]\REBORN2_DISC9\BDMV\STREAM\00002.m2ts")
src_jp = src_jp[:2698] # for cutting audio

src_us = lvf.src(r"REBORN CS BD\REBORN SEASONS 1-4 BD\REBORN SEASONS 1-4 D2\BDMV\STREAM\00055.m2ts")
src_us = core.std.CropRel(src_us, 4, 4, 0, 0)
src_us = fvf.Depth(src_us, 16)

src_us = kgf.insert_clip(src_us, src_us[1712], 1711)
#src_us = kgf.insert_clip(src_us, src_us[1973], 1974)

nn3 = core.nnedi3.nnedi3(src_us, field=0)
w2x = fvf.Depth(nn3, 32) # If throwing away fields destroys too much detail, just reinvent new detail! ヽ( ﾟヮ・)ノ
w2x = fvf.Depth(core.resize.Spline36(core.w2xc.Waifu2x(w2x, noise=2, scale=2, gpu=2), 712, 480), 16)
src_us = fvf.rfs(src_us, w2x, mappings="[869 912] [1527 1529] [1655 1672] [1691 1709]")

dehalo = haf.FineDehalo(src_us, rx=2, thmi=250, thma=255, thlimi=64, thlima=100)

scaled = nnedi3_rpow2(dehalo)
scaled = core.resize.Spline36(scaled, 960, 720, matrix_s='709')

denoised_a = lvf.denoise(scaled, h=0.8)
denoised_b = lvf.denoise(scaled, h=1.6, sigma=5)
denoised = fvf.rfs(denoised_a, denoised_b, mappings="[148 804] [817 1066] [1385 1709]")

sharp = haf.LSFmod(denoised, strength=140, soft=10, edgemode=1, Smethod=2, Lmode=2)

darken = haf.FastLineDarkenMOD(sharp, strength=48)
darken = fvf.rfs(sharp, darken, mappings="[148 243] [544 804]")

aa_a = taa.TAAmbk(darken, aatype='Eedi3')
aa_b = taa.TAAmbk(darken, preaa=1, aatype='Nnedi3')
aa = fvf.rfs(aa_a, aa_b, mappings="[898 912]")

deband_a = core.f3kdb.Deband(aa, range=16, y=48, cb=40, cr=40, grainy=12, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(aa, range=18, y=64, cb=56, cr=56, grainy=12, grainc=0, output_depth=16)
deband_c = core.f3kdb.Deband(aa, range=5, y=160, cb=152, cr=152, grainy=0, grainc=0, output_depth=16)
deband_c = core.f3kdb.Deband(deband_c, range=18, y=56, cb=48, cr=48, grainy=24, grainc=0, output_depth=16)
deband_d = core.f3kdb.Deband(aa, range=21, y=72, cb=64, cr=64, grainy=0, grainc=0, output_depth=16)
deband = fvf.rfs(deband_a, deband_b, mappings="[829 896] [913  [1661 1709]")
deband = fvf.rfs(deband, deband_c, mappings="[817 849] [1784 1851]")
deband = fvf.rfs(deband, deband_d, mappings="[165 268]")

grain_a = kgf.adaptive_grain(deband, 0.1)
grain_b = kgf.adaptive_grain(deband, 1)
grain_c = kgf.adaptive_grain(deband, 2)
grain = fvf.rfs(grain_a, grain_b, mappings="[0 142] [817 849] [1784 1851]")
grain = fvf.rfs(grain, grain_c, mappings="[829 849]")

out = grain
final = fvf.Depth(out, 10)
final.set_output()