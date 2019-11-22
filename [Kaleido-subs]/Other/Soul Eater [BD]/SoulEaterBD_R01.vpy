import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import havsfunc as haf
import vsTAAmbk as taa
import mvsfunc as mvf
import vsutil
core = vs.core
core.num_threads = 2
core.max_cache_size = 8192

opstart, edstart = 1651, 31049


src_a = lvf.src(r'G:/src/[BDMV][Soul Eater]/Soul_Eater_Complete/Soul_Eater_BDBox1/SOUL_EATER_01/BDMV/STREAM/00000.m2ts')
src_b = lvf.src(r'G:/src/[BDMV][Soul Eater]/Soul_Eater_Complete/Soul_Eater_BDBox1/SOUL_EATER_04/BDMV/STREAM/00038.m2ts')
src_c = lvf.src(r'G:/src/[BDMV][Soul Eater]/Soul_Eater_Complete/Soul_Eater_BDBox1/SOUL_EATER_01/BDMV/STREAM/00002.m2ts')
src_d = lvf.src(r'G:/src/[BDMV][Soul Eater]/Soul_Eater_Complete/Soul_Eater_BDBox1/SOUL_EATER_01/BDMV/STREAM/00003.m2ts')
src_e = lvf.src(r'G:/src/[BDMV][Soul Eater]/Soul_Eater_Complete/Soul_Eater_BDBox1/SOUL_EATER_01/BDMV/STREAM/00005.m2ts')

ncop = src_b[9336:11496]
nced = src_b[11616:13776]


# This can probably be done way neater.
src = src_a+ncop+src_c+src_d+nced+src_e
src = core.edgefixer.ContinuityFixer(src, 4, 4, 4, 4)
src_a = lvf.conditional_descale(src, height=540, b=0, c=1, w2x=True)
src_b = fvf.Depth(core.resize.Spline36(src, src_a.width, src_a.height), 32)
src = fvf.rfs(src_a, src_b, mappings=f"[{opstart} {opstart+2159}] [{edstart} {edstart+2159}]")


# 1080p isn't worth it for this show, so I'm just going with 720p 444.
scaled = core.resize.Bicubic(src, 1280, 720, format=vs.YUV444P16, filter_param_a=0, filter_param_b=1/2)


# The fun ends here. It's just a generic filterchain from this point onwards.
denoise = mvf.BM3D(scaled, sigma=[2.5,1])
denoise = fvf.rfs(denoise, scaled, mappings=f"[{edstart} {edstart+2157}]")

aa_a = lvf.NnEedi3(denoise, opencl=True)
aa_b = taa.TAAmbk(denoise, aatype='Nnedi3SangNom', sharp=120, repair=2, cycle=1)
aa = fvf.rfs(aa_a, aa_b, mappings="[11096 11168]")

deband_a = core.f3kdb.Deband(aa, range=16, y=32, cb=24, cr=24, grainy=24, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(aa, range=18, y=56, cb=48, cr=48, grainy=48, grainc=0, output_depth=16)
deband = fvf.rfs(deband_a, deband_b, mappings=f"[{opstart+870} {opstart+915}] [{opstart+1094} {opstart+1163}] [{opstart+1647} {opstart+1721}] [{opstart+1977} {opstart+2036}] [6542 6584] [11137 11164] [20306 20393] [29819 30023] [30208 30862]")

grain = kgf.adaptive_grain(deband, 0.5, luma_scaling=4)


out = grain
final = fvf.Depth(out, 10)
final.set_output()
