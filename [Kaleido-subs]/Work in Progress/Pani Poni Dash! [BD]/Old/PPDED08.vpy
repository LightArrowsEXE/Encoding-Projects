import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import vsTAAmbk as taa
import havsfunc as haf
import finesharp
core = vs.core

NCED = lvf.src(r"[BDMV][Pani Poni Dash][ぱにぽにだっしゅ！]\VOL6\BDMV\STREAM\00024.m2ts")
NCED = NCED[24:2182]
NCED = core.std.CropRel(NCED, 20, 20, 8, 6)
NCED = fvf.Depth(NCED, 16)

NCED = core.resize.Spline36(NCED, 1280, 720, format=vs.YUV444P16)

ed_denoise = lvf.denoise(NCED, h=1.6, sigma=5)
ed_csharp = haf.LSFmod(ed_denoise, strength=80, soft=10, edgemode=1, Smethod=2, Lmode=2)
ed_aa = taa.TAAmbk(ed_csharp, aatype='Eedi3')

final = fvf.Depth(ed_aa, 10)
final.set_output()