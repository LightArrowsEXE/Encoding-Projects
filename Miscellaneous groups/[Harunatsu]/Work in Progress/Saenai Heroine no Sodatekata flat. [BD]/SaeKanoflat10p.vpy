import vapoursynth as vs
import kagefunc as kgf
import vsTAAmbk as taa
import lvsfunc as lvf
import fvsfunc as fvf
import havsfunc as haf
core = vs.core

opstart = 0
opend = 2158
edstart = 30691
edend = 32848

src = lvf.src(r"[BDMV]冴えない彼女の育てかた♭Vol.01~Vol.06/[BDMV]冴えない彼女の育てかた♭ VOL.06 Fin/BDMV/STREAM/00001.m2ts")
src = src[24:32872]
src = fvf.Depth(src, 16)

src_ed = lvf.src(r"[BDMV]冴えない彼女の育てかた♭Vol.01~Vol.06/[BDMV]冴えない彼女の育てかた♭ VOL.01/BDMV/STREAM/00010.m2ts")
src_ed = src_ed[24:2184]
src_ed = fvf.Depth(src_ed, 16)

blank = core.std.BlankClip(src)
blank = blank[0]

# # # # # # # # ED filtering # # # # # # # #

ed_denoised = lvf.qden(src_ed, h=0.4)
ed_denoised = haf.ContraSharpening(ed_denoised, src_ed)

ed_aa = taa.TAAmbk(ed_denoised, aatype='Eedi3', opencl=True)
ed_deband = core.f3kdb.Deband(ed_aa, range=16, y=48, cr=40, cb=40, grainy=0, grainc=0, output_depth=16)

ed_grain = kgf.adaptive_grain(ed_deband, 0.5)

ed_out = blank*edstart+ed_grain
ed_out = ed_out[edstart:edend]

out = kgf.insert_clip(src, ed_out, edstart)
final = fvf.Depth(out, 10)

p = lvf.src(r"F:\Portfolio\__Github\Encoding-Projects\[Harunatsu]\Work in Progress\Saenai Heroine no Sodatekata flat. [BD]\encodes\SaeKanoflat10.mkv")
comp = lvf.comp(src, out, [31651, 31651+500, 31651+1000])
patch = final[31651:]
comp.set_output()