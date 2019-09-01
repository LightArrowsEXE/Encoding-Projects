import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
from nnedi3_rpow2 import nnedi3_rpow2
from vsTAAmbk import TAAmbk
from vsutil import get_w
core = vs.core

# Note: before cutting
preview = 16688
endcard = 16808
part_b = 16928
epend = 20236

# Note: after cutting
edstart = 15586


src = lvf.src(r"BDMV/[BDMV][190302][マナリアフレンズ I]/BD/BDMV/STREAM/00007.m2ts")
blank = core.std.BlankClip(src) # Part B starts too abruptly, so there's some space for a breather after ED.
src = src[24:preview]+blank[:48]+src[part_b:]+src[preview:part_b]


scaled = kgf.inverse_scale(src, height=878, kernel='bicubic', b=0, c=1,
        denoise=True, use_gpu=False, bm3d_sigma=[3,1.5],
        mask_detail=True)
scaled = fvf.Depth(scaled, 16)

aa_a = TAAmbk(scaled, aatype='Eedi3')
aa_b = TAAmbk(scaled, aatype='Nnedi3SangNom', cycle=3) # w h y y y y y y
aa = fvf.rfs(aa_a, aa_b, mappings="[1053 1091]")

deband = core.f3kdb.Deband(aa, range=15, y=32, cb=24, cr=24, grainy=12, grainc=0, output_depth=16)
grain = kgf.adaptive_grain(deband, 0.2, luma_scaling=8)


out = grain
final = fvf.Depth(out, 10)
final.set_output()
