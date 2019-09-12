import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import mvsfunc as mvf
from vsTAAmbk import TAAmbk
core = vs.core

opstart, edstart = None, 32344

src = lvf.src(r'G:\src\[BDMV] Lord El-Melloi II Sei no Jikenbo\Vol 1\BDROM\BDMV\STREAM\00001.m2ts')
src = src[24:-24]
src = fvf.Depth(src, 16)


scaled = kgf.inverse_scale(src, height=720, kernel='bicubic', b=0, c=1/2, 
         mask_detail=True, descale_mask_zones=f"""[32683 {src.num_frames-1}]]
                                                  [0 4160] [15728 15799]""")

denoise = fvf.Depth(mvf.BM3D(scaled, sigma=[1.5,0.8]), 16)

mask = kgf.retinex_edgemask(denoise)
merge = core.std.MaskedMerge(denoise, fvf.Depth(scaled, 16), mask)

aa = lvf.nneedi3_clamp(merge, mask=mask.std.Maximum(), strength=1.7)
deband = core.f3kdb.Deband(aa, range=15, y=32, cb=24, cr=24, grainy=56, grainc=0, output_depth=16)
grain = kgf.adaptive_grain(deband, 0.15, luma_scaling=6)


out = grain
final = fvf.Depth(out, 10)
final.set_output()
