import vapoursynth as vs
import vsTAAmbk as taa
import kagefunc as kgf
import fvsfunc as fvs
from nnedi3_rpow2 import nnedi3_rpow2
core = vs.get_core()

src = r"F:\Convert\[BDMV][180328]スロウスタート Vol.1\BD\BDMV\STREAM\00002.m2ts"
OP = r"F:\Convert\[BDMV][180328]スロウスタート Vol.1\BD\BDMV\STREAM\00005.m2ts"
ED = r"F:\Convert\[BDMV][180328]スロウスタート Vol.1\BD\BDMV\STREAM\00007.m2ts"

epstart = 0
partb = 18053
epend = 34548
opstart = 2086
opend = 4244
edstart = 32032
edend = 34188

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
aa = core.remap.Rfs(scaled, aa_1, mappings=f"[{edstart+1940} {edend}] [17472 17507]")
aa = core.remap.Rfs(aa, aa_2, mappings=f"[418 539] [4465 4604] [6561 6680] [8321 8402] [22543 22658] [23083 23128] [23488 23654] [26510 26566] [26783 26848] [27495 27829] [28625 28737] [29408 29544] [29674 29852] [29998 30372]")

low_deband = core.f3kdb.Deband(aa, range=14, y=32, cb=24, cr=24, grainy=0, grainc=0, output_depth=16)
med_deband = core.f3kdb.Deband(aa, range=16, y=40, cb=32, cr=32, grainy=0, grainc=0, output_depth=16)
high_deband = core.f3kdb.Deband(aa, range=19, y=72, cb=64, cr=64, grainy=24, grainc=0, output_depth=16)
autism_deband = core.f3kdb.Deband(aa, range=5, y=80, cb=72, cr=72, grainy=0, grainc=0, output_depth=16)
autism_deband = core.f3kdb.Deband(autism_deband, range=14, y=64, cb=56, cr=56, grainy=24, grainc=0, output_depth=16)
autism_deband_mkII = core.f3kdb.Deband(aa, range=5, y=120, cb=112, cr=112, grainy=0, grainc=0, output_depth=16)
autism_deband_mkII = core.f3kdb.Deband(autism_deband_mkII, range=23, y=72, cb=64, cr=64, grainy=64, grainc=0, output_depth=16)
deband = core.remap.Rfs(low_deband, med_deband, mappings="[5402 5569] [10447 10560] [11061 11159] [17104 17213] [20525 23654] [23937 24041] [25883 26194]")
deband = core.remap.Rfs(deband, high_deband, mappings=f"[5939 6043] [6306 6370] [6561 6680] [17214 17265] [17813 17913] [22359 22430] [22543 22658] [23035 23082] [23129 23224] [23488 23547] [23601 23654] [26921 27261]")
deband = core.remap.Rfs(deband, autism_deband, mappings=f"[{opstart+82} {opstart+98}] [7067 7222] [7403 7524] [7897 7974] [8564 8749] [9254 9406] [17424 17471] [18146 18367] [19404 19475] [29853 29927]")
deband = core.remap.Rfs(deband, autism_deband_mkII, mappings=f"[{opstart+99} {opstart+120}] [0 56] [7745 7842] [8064 8188] [18053 18145] [24712 24773] [31737 31911]")

light_grain = kgf.adaptive_grain(deband, 0.2, luma_scaling=8)
heavy_grain = kgf.adaptive_grain(deband, 0.6, luma_scaling=8)
more_heavy_grain = kgf.adaptive_grain(deband, 1, luma_scaling=4)
grain = core.remap.Rfs(deband, light_grain, mappings=f"[{opstart+99} {opstart+120}] [7745 7842] [8064 8188] [9254 9406] [24762 24773]")
grain = core.remap.Rfs(grain, heavy_grain, mappings=f"[{opstart+82} {opstart+98}] [8064 8188] [31737 31911]")
grain = core.remap.Rfs(grain, more_heavy_grain, mappings="[18053 18145]")

endcard = core.remap.Rfs(grain, src, mappings=restore_endcard)

final = fvs.Depth(endcard, 10, dither_type='error_diffusion')
luma = kgf.getY(final)
test = final[31850:31911]
final.set_output()