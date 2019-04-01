import vapoursynth as vs
import lvsfunc as lvf
import fvsfunc as fvf
import kagefunc as kgf
import vsTAAmbk as taa
core = vs.core

src = lvf.src("/run/media/lightarrowsexe/Seagate Expansion Drive/Encode/[DVDISO][Cardcaptor Sakura Clear Card-hen OVA]/ClearCardOVA-CRrip.mp4")

scaled_a = kgf.inverse_scale(src, height=720, kernel='bicubic', kerneluv='blackman',
                  a1=0, a2=1, mask_detail=True, masking_areas=[[2268,2412],[35119,36856]])
scaled_b = core.resize.Spline36(src, 1280, 720, format=vs.YUV444PS)
scaled = fvf.rfs(scaled_a, scaled_b, mappings="[1893 1982] [10497 10760] [38090 38269]")
scaled = fvf.Depth(scaled, 16)

srcY, srcU, srcV = kgf.split(scaled)
srcU = core.resize.Spline36(srcU, 640, 360)
srcV = core.resize.Spline36(srcV, 640, 360)
scaled = kgf.join([scaled, srcU, srcV])


aa = taa.TAAmbk(scaled, aatype='Nnedi3', opencl=True)
aa = fvf.rfs(scaled, aa, mappings="[1893 1982] [10497 10760] [13668 13976] [34381 34434] [38090 38269]")

deband_a = core.f3kdb.Deband(aa, range=14, y=32, cb=24, cr=24, grainy=0, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(aa, range=16, y=40, cb=32, cr=32, grainy=12, grainc=0, output_depth=16)
deband_c = core.f3kdb.Deband(aa, range=16, y=56, cb=48, cr=48, grainy=12, grainc=0, output_depth=16)
deband = fvf.rfs(deband_a, deband_b, mappings="[7708 8108] [8907 9044]")
deband = fvf.rfs(deband, deband_c, mappings="[29516 29563]")


grain = kgf.adaptive_grain(deband, 1, static=False)
grain = fvf.rfs(deband, grain, mappings="[2268 2412] [7708 7836] [22416 23158]")

out = grain
final = fvf.Depth(grain, 10)
final = final[31986:36902]
final.set_output()