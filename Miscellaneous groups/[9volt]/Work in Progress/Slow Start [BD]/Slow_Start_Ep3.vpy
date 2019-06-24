import vapoursynth as vs
import vsTAAmbk as taa
import kagefunc as kgf
import fvsfunc as fvs
from nnedi3_rpow2 import nnedi3_rpow2
core = vs.get_core()

src = r"F:\Convert\[BDMV][180425]スロウスタート Vol.2\BD\BDMV\STREAM\00001.m2ts"
OP = r"F:\Convert\[BDMV][180328]スロウスタート Vol.1\BD\BDMV\STREAM\00005.m2ts"
ED = r"F:\Convert\[BDMV][180425]スロウスタート Vol.2\BD\BDMV\STREAM\00004.m2ts"

epstart = 0
opstart = 1080
opend = 3236
edstart = 32032
edend = 34188
epend = 34548

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

eptitle = f"[{opend+1}, {opend+500}]"

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

scaled = kgf.inverse_scale(src, width=None, height=864, kernel='spline16', mask_detail=True, masking_areas=[[opend+1,opend+500]])
scaled = nnedi3_rpow2(scaled, rfactor=2)
scaled = core.resize.Spline36(scaled, 1920, 1080, format=vs.YUV420P16)
scaled = kgf.join([scaled, srcU, srcV])

aa_1 = taa.TAAmbk(scaled, aatype='Nnedi3', opencl=True, cycle=0)
aa_2 = taa.TAAmbk(scaled, aatype='Eedi3', opencl=True, cycle=0)
aa = core.remap.Rfs(scaled, aa_1, mappings=f"[{edstart+1940} {edend}] [26919 26954]")
aa = core.remap.Rfs(aa, aa_2, mappings=f"[3404 3583] [3872 3973] [4521 4615] [4957 5199] [6313 6483] [6804 6892] [11775 11846] [12872 12931] [13052 13168] [13375 13479] [13626 13721] [15093 15319] [16344 16403] [24496 24539] [25866 26153] [26511 26598] [26955 27040] [27275 27322] [27454 27660] [27931 28097] [28609 28732] [29097 29168] [29595 29672] [29745 29792] [30698 30918] [31273 31342]")


low_deband = core.f3kdb.Deband(aa, range=14, y=32, cb=24, cr=24, grainy=0, grainc=0, output_depth=16)
med_deband = core.f3kdb.Deband(aa, range=16, y=40, cb=32, cr=32, grainy=0, grainc=0, output_depth=16)
high_deband = core.f3kdb.Deband(aa, range=19, y=72, cb=64, cr=64, grainy=24, grainc=0, output_depth=16)
autism_deband = core.f3kdb.Deband(aa, range=5, y=80, cb=72, cr=72, grainy=0, grainc=0, output_depth=16)
autism_deband = core.f3kdb.Deband(autism_deband, range=14, y=64, cb=56, cr=56, grainy=24, grainc=0, output_depth=16)
autism_deband_mkII = core.f3kdb.Deband(aa, range=5, y=120, cb=112, cr=112, grainy=0, grainc=0, output_depth=16)
autism_deband_mkII = core.f3kdb.Deband(autism_deband_mkII, range=23, y=72, cb=64, cr=64, grainy=64, grainc=0, output_depth=16)
deband = core.remap.Rfs(low_deband, med_deband, mappings="[17709 17814] [31273 31342]")
deband = core.remap.Rfs(deband, high_deband, mappings="[864 1079] [11571 11594] [11928 12023] [12195 12404] [12627 12871] [13052 13168] [30506 30661] [30698 30966]")
deband = core.remap.Rfs(deband, autism_deband, mappings=f"[{opstart+82} {opstart+98}] [0 59] [9424 9471] [10658 10705] [11042 11278] [30967 31044]")
deband = core.remap.Rfs(deband, autism_deband_mkII, mappings=f"[{opstart+99} {opstart+120}] [14255 14324] [29793 29834]")

light_grain = kgf.adaptive_grain(deband, 0.2, luma_scaling=8)
heavy_grain = kgf.adaptive_grain(deband, 0.6, luma_scaling=8)
more_heavy_grain = kgf.adaptive_grain(deband, 1, luma_scaling=4)
grain = core.remap.Rfs(deband, light_grain, mappings=f"[{opstart+99} {opstart+120}] [14255 14324] [29793 29834]")
grain = core.remap.Rfs(grain, heavy_grain, mappings=f"[{opstart+82} {opstart+98}] [0 0]")
grain = core.remap.Rfs(grain, more_heavy_grain, mappings="[0 0]")

endcard = core.remap.Rfs(grain, src, mappings=restore_endcard)

final = fvs.Depth(endcard, 10, dither_type='error_diffusion')
luma = kgf.getY(final)
test = final[31850:31911]
srcY.set_output()