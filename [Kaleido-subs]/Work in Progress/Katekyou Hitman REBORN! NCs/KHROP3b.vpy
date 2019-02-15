import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import havsfunc as haf
import vsTAAmbk as taa
from nnedi3_rpow2 import nnedi3_rpow2
core = vs.core

src_jp = lvf.src(r"[BDMV][Katekyou Hitman REBORN!]\[家庭教師ヒットマンREBORN！][2006][TV][BDMV][Blu-ray BOX 1][JP][20170419]\REBORN_DISC9\BDMV\STREAM\00005.m2ts")
src_jp = src_jp[:2698] # for cutting audio

src_us = lvf.src(r"REBORN CS BD\REBORN SEASONS 1-4 BD\REBORN SEASONS 1-4 D2\BDMV\STREAM\00054.m2ts")
src_us = core.std.AssumeFPS(src_us, fpsnum=24000, fpsden=1001)
src_us = core.std.CropRel(src_us, 4, 4, 0, 0)
src_us = fvf.Depth(src_us, 16)

src_us = kgf.insert_clip(src_us, src_us[1441], 1442)
src_us = kgf.insert_clip(src_us, src_us[1393], 1394)
src_us = kgf.insert_clip(src_us, src_us[164], 165)
src_us = kgf.insert_clip(src_us, src_us[520], 521)
src_us = kgf.insert_clip(src_us, src_us[1250], 1249)

c_scaled = nnedi3_rpow2(src_us) # Scaled for comparison
c_scaled = core.resize.Spline36(c_scaled, 960, 720, matrix_s='709')

dehalo = haf.FineDehalo(src_us, rx=2, thmi=250, thma=255, thlimi=64, thlima=100)

scaled = nnedi3_rpow2(dehalo)
scaled = core.resize.Spline36(scaled, 960, 720, matrix_s='709')

denoised = lvf.denoise(scaled, h=0.8)
contrasharp = haf.ContraSharpening(denoised, scaled)
contrasharp = fvf.rfs(denoised, contrasharp, mappings="[955 1025]")
denoised_b = lvf.denoise(scaled, h=2, sigma=8) # The titlecard has some annoying background artifacting. This doesn't get rid of it entirely, but I don't want to murder everything either.
early_deband = core.f3kdb.Deband(denoised_b, range=23, y=48, cb=40, cr=40, grainy=12, grainc=0, output_depth=16)
denoised = fvf.rfs(contrasharp, early_deband, mappings="[303 475]")

sharp = haf.LSFmod(denoised, strength=140, soft=10, edgemode=1, Smethod=2, Lmode=2)
aa = taa.TAAmbk(sharp, aatype='Eedi3')

deband = core.f3kdb.Deband(aa, range=16, y=48, cb=40, cr=40, grainy=12, grainc=0, output_depth=16)

grain_a = kgf.adaptive_grain(deband, 1) # might just be me, but I really like the dynamic grain on that one cut :notlikemiya:
grain_b = kgf.adaptive_grain(deband, 10, static=False)
grain = fvf.rfs(grain_a, grain_b, mappings="[955 1025]")

out = grain
final = fvf.Depth(out, 10)
final.set_output()