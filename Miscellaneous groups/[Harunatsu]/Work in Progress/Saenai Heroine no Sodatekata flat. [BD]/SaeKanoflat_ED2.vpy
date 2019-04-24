import vapoursynth as vs
import kagefunc as kgf
import vsTAAmbk as taa
import lvsfunc as lvf
import fvsfunc as fvf
import havsfunc as haf
core = vs.core

src_ed = lvf.src(r"[BDMV]冴えない彼女の育てかた♭Vol.01~Vol.06/[BDMV]冴えない彼女の育てかた♭ VOL.06 Fin/BDMV/STREAM/00009.m2ts")
src_ed = src_ed[24:2182]
src_ed = fvf.Depth(src_ed, 16)

ed_denoised = lvf.denoise(src_ed, h=0.4)
ed_denoised = haf.ContraSharpening(ed_denoised, src_ed)

ed_aa = taa.TAAmbk(ed_denoised, aatype='Eedi3', opencl=True)
ed_deband = core.f3kdb.Deband(ed_aa, range=16, y=48, cr=40, cb=40, grainy=12, grainc=0, output_depth=16)
ed_grain = kgf.adaptive_grain(ed_deband, 0.5)

out = ed_grain
final = fvf.Depth(out, 10)
final.set_output()