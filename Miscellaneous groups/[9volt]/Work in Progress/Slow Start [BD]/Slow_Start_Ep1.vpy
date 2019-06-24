import vapoursynth as vs
import vsTAAmbk as taa
import kagefunc as kgf
import fvsfunc as fvs
from nnedi3_rpow2 import nnedi3_rpow2
core = vs.get_core()

src = r"F:\Convert\[BDMV][180328]スロウスタート Vol.1\BD\BDMV\STREAM\00001.m2ts"
OP = r"F:\Convert\[BDMV][180328]スロウスタート Vol.1\BD\BDMV\STREAM\00005.m2ts"
ED = r"F:\Convert\[BDMV][180328]スロウスタート Vol.1\BD\BDMV\STREAM\00006.m2ts"

epstart = 0
epend = 34547
opstart = 2614
opend = 4770
edstart = 31407
edend = 33565

oplength = opend-opstart
oplength = 0+oplength+1
edlength = edend-edstart
edlength = 0+edlength+1
endcardlength = 119
edsponsorlength = 240

opsponsorstart = opend+1
opsponsorend = opend+121
edsponsorstart = epend-(endcardlength+edsponsorlength)
edsponsorend = epend-endcardlength

sponsorlength = 119+240
restore_endcard = f"[{epend-endcardlength-sponsorlength-1} {epend-sponsorlength-1}]"

eptitle = f"[{opsponsorend+1} {opsponsorend+500}]"

src = core.lsmas.LWLibavSource(src)
src = src[epstart:opsponsorstart] + src[opsponsorend:edsponsorstart] + src[edsponsorend:epend+1]

OP = core.lsmas.LWLibavSource(OP)
OP = OP[0:2160]
OP = OP[epstart:oplength]
ED = core.lsmas.LWLibavSource(ED)
ED = ED[24:2184]
ED = ED[epstart:edlength]

src = kgf.insert_clip(src, OP, opstart)
src = kgf.insert_clip(src, ED, edstart-120)
src = fvs.Depth(src, 16)
srcY, srcU, srcV = kgf.split(src)

scaled = kgf.inverse_scale(src, width=None, height=864, kernel='spline16')
scaled = nnedi3_rpow2(scaled, rfactor=2)
scaled = core.resize.Spline36(scaled, 1920, 1080, format=vs.YUV420P16)
scaled = kgf.join([scaled, srcU, srcV])

aa_1 = taa.TAAmbk(scaled, aatype='Nnedi3', opencl=True, cycle=0)
aa_2 = taa.TAAmbk(scaled, aatype='Eedi3', opencl=True, cycle=0)
aa = core.remap.Rfs(scaled, aa_1, mappings=f"[{edstart+1940} {edend}] [9168 9371] [9959 10066] [10498 10557] [24333 24527] [29658 29789]")
aa = core.remap.Rfs(aa, aa_2, mappings=f"[9168 9371] [11813 11953] [28469 28607] [29658 29789] [29991 30116]")

low_deband = core.f3kdb.Deband(aa, range=14, y=32, cb=24, cr=24, grainy=0, grainc=0, output_depth=16)
med_deband = core.f3kdb.Deband(aa, range=16, y=40, cb=32, cr=32, grainy=0, grainc=0, output_depth=16)
high_deband = core.f3kdb.Deband(aa, range=19, y=72, cb=64, cr=64, grainy=24, grainc=0, output_depth=16)
autism_deband = core.f3kdb.Deband(aa, range=5, y=80, cb=72, cr=72, grainy=0, grainc=0, output_depth=16)
autism_deband = core.f3kdb.Deband(autism_deband, range=14, y=64, cb=56, cr=56, grainy=24, grainc=0, output_depth=16)
autism_deband_mkII = core.f3kdb.Deband(aa, range=5, y=120, cb=112, cr=112, grainy=0, grainc=0, output_depth=16)
autism_deband_mkII = core.f3kdb.Deband(autism_deband_mkII, range=23, y=72, cb=64, cr=64, grainy=64, grainc=0, output_depth=16)
deband = core.remap.Rfs(low_deband, med_deband, mappings="[1752 1784] [1820 1950] [10819 10992] [12939 13012] [21489 21590] [30917 31054]")
deband = core.remap.Rfs(deband, high_deband, mappings=f"[943 1001] [1951 1986] [18939 19115]")
deband = core.remap.Rfs(deband, autism_deband, mappings=f"[{opstart+82} {opstart+98}] [21011 21052] [30117 30207]")
deband = core.remap.Rfs(deband, autism_deband_mkII, mappings=f"[{opstart+99} {opstart+120}]")

light_grain = kgf.adaptive_grain(deband, 0.2, luma_scaling=8)
heavy_grain = kgf.adaptive_grain(deband, 0.6, luma_scaling=8)
grain = core.remap.Rfs(deband, light_grain, mappings=f"[{opstart+99} {opstart+120}] [943 1001] [9959 10290] [13283 13378] [21011 21052] [30469 30504]")
grain = core.remap.Rfs(deband, heavy_grain, mappings=f"[{opstart+82} {opstart+98}]")

endcard = core.remap.Rfs(grain, src, mappings=restore_endcard)

final = fvs.Depth(endcard, 10, dither_type='error_diffusion')
luma = kgf.getY(final)
test = final[opstart:opend-1]
final.set_output()