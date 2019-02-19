import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import havsfunc as haf
import vsTAAmbk as taa
from nnedi3_rpow2 import nnedi3_rpow2
core = vs.core

#opstart = 0
#edstart = 31048

src_jp = lvf.src(r"../[家庭教師ヒットマンREBORN！][2006][TV][BDMV][Blu-ray BOX 1][JP][20170419]/REBORN_DISC1/BDMV/STREAM/00001.m2ts")
src_jp = src_jp[293904:335860] # for cutting audio

src_us = lvf.src(r"../REBORN CS BD/REBORN SEASONS 1-4 BD/REBORN SEASONS 1-4 D1/BDMV/STREAM/00007.m2ts")
src_us = core.std.CropRel(src_us, 4, 4, 0, 0)
src_us = fvf.Depth(src_us, 16)

src_us = kgf.insert_clip(src_us, src_us[opstart+1085], opstart+1084)

nn3 = core.nnedi3.nnedi3(src_us, field=0)
w2x = fvf.Depth(nn3, 32) # If throwing away fields destroys too much detail, just reinvent new detail! ヽ( ﾟヮ・)ノ
w2x = fvf.Depth(core.resize.Spline36(core.w2xc.Waifu2x(w2x, noise=1, scale=2, gpu=2), 712, 480), 16)
nn3 = fvf.rfs(src_us, w2x, mappings=f"[{opstart+2112} {opstart+2152}] ")

mask = core.resize.Spline36(core.imwri.Read(r"!OPED/KHROP1a_mask.png"), 712, 480, format=vs.GRAY16, matrix_s='709')
nn3_m = core.std.MaskedMerge(nn3, src_us, mask)
nn3 = fvf.rfs(nn3, nn3_m, mappings=f"[{opstart+2112} {opstart+2152}]")

scaled_nn3rp2 = nnedi3_rpow2(nn3)
scaled = core.resize.Spline36(scaled_nn3rp2, 960, 720, matrix_s='709')

# # # # OP Filtering # # # #
op = scaled[opstart:opstart+2153]

op_denoised = lvf.denoise(op, h=1.6)

op_sharp = haf.LSFmod(op_denoised, strength=140, soft=10, edgemode=1, Smethod=2, Lmode=2)

op_aa = taa.TAAmbk(op_sharp, aatype='Eedi3')

op_deband = core.f3kdb.Deband(op_aa, range=16, y=48, cb=40, cr=40, grainy=12, grainc=0, output_depth=16)

op_grain = kgf.adaptive_grain(op_deband, 0.1)
# # # # OP Filtering # # # #
# # # # ED Filtering # # # #
ed = scaled[edstart:]
ed_denoised = lvf.denoise(ed, h=0.8)

ed_sharp = haf.LSFmod(ed_denoised, strength=140, soft=10, edgemode=1, Smethod=2, Lmode=2)

ed_aa = taa.TAAmbk(ed_sharp, aatype='Eedi3')

ed_deband = core.f3kdb.Deband(ed_aa, range=16, y=48, cb=40, cr=40, grainy=12, grainc=0, output_depth=16)
# # # # ED Filtering # # # #

denoised = lvf.denoise(scaled, h=0.4)

sharp = haf.LSFmod(denoised, strength=140, soft=10, edgemode=1, Smethod=2, Lmode=2)

aa = taa.TAAmbk(sharp, aatype='Nnedi3')

deband = core.f3kdb.Deband(aa, range=14, y=48, cb=40, cr=40, grainy=12, grainc=0, output_depth=16)


out = deband
out = kgf.insert_clip(out, op_grain, opstart)
out = kgf.insert_clip(out, ed_deband[:-1], edstart)
final = fvf.Depth(out, 10)
final.set_output()