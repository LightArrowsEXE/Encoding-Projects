import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
from vsTAAmbk import TAAmbk
core = vs.core

opstart, edstart = 1176, 38976

src = lvf.src(r'YURUYURI_10/BDMV/STREAM/00000.m2ts')
src = src[:-24]
src = core.edgefixer.ContinuityFixer(src, 1, 1, 1, 1, 2)
src = fvf.Depth(src, 16)


scaled = kgf.inverse_scale(src, height=720, 
                           kernel='bicubic', b=0, c=1/2,
                           mask_detail=True, denoise=True, use_gpu=False,
                           descale_mask_zones=f"[{opstart} {opstart+2159}] [{edstart} {edstart+5183}]",
                           bm3d_sigma=1.5)
scaled = fvf.Depth(scaled, 16)

aa = TAAmbk(scaled, aatype='Nnedi3', repair=2)
deband = core.f3kdb.Deband(aa, range=15, y=32, cb=24, cr=24, grainy=0, grainc=0, output_depth=16)


out = deband
final = fvf.Depth(out, 10)
final.set_output()
