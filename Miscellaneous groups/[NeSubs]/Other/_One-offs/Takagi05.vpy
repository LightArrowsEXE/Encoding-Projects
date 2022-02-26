import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import vsTAAmbk as taa
core = vs.core

opstart, edstart = 0, 31888


src = lvf.src(r"G:/src/[Better-Raws] Karakai Jouzu no Takagi-san S2 - 05 (NF 1920x1080 x264 EAC3).mkv")
src = src[24:-23]
src = fvf.Depth(src, 16)


# "Cheaper" form of denoising. Allows for way faster encoding at the cost of... 
# well, not being a proper denoiser. Gets the job done, though.
d_mask = kgf.adaptive_grain(src, show_mask=True, luma_scaling=4)
deblock = core.deblock.Deblock(src, quant=30)
deblock = core.std.MaskedMerge(src, deblock, d_mask)


# Why do so many seasonals have such shit lineart and can't be descaled well-enough to remedy that?
edge_mask = kgf.retinex_edgemask(src, 0.1)
aa = taa.TAAmbk(deblock, aatype='Nnedi3SangNom', sharp=120, repair=0)
aa = core.std.MaskedMerge(deblock, aa, edge_mask)
aa = fvf.rfs(aa, deblock, mappings=f"[{opstart} {opstart+2157}] [{edstart} {edstart+2158}]")

deband = core.f3kdb.Deband(aa, range=16, y=32, cb=24, cr=24, grainy=0, grainc=0, output_depth=16)
grain = kgf.adaptive_grain(deband, 0.3)


out = grain
final = fvf.Depth(out, 10)
final.set_output()
