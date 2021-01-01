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


def descale_oped(src):
    src = fvf.Depth(src, 32)
    y, u, v = kgf.split(src)
    descaled = kgf.inverse_scale(y, height=540, kernel='bicubic', b=0, c=1, mask_detail=True)
    w2x = core.caffe.Waifu2x(descaled, noise=-1, scale=2, model=6, cudnn=True, processor=0, tta=False)
    return kgf.join([w2x, u, v])


src_a = lvf.src(r'G:/src/[BDMV][Soul Eater]/Soul_Eater_Complete/Soul_Eater_BDBox1/SOUL_EATER_01/BDMV/STREAM/00000.m2ts')
src_b = lvf.src(r'G:/src/[BDMV][Soul Eater]/Soul_Eater_Complete/Soul_Eater_BDBox1/SOUL_EATER_01/BDMV/STREAM/00001.m2ts')
src_c = lvf.src(r'G:/src/[BDMV][Soul Eater]/Soul_Eater_Complete/Soul_Eater_BDBox1/SOUL_EATER_01/BDMV/STREAM/00002.m2ts')
src_d = lvf.src(r'G:/src/[BDMV][Soul Eater]/Soul_Eater_Complete/Soul_Eater_BDBox1/SOUL_EATER_01/BDMV/STREAM/00003.m2ts')
src_e = lvf.src(r'G:/src/[BDMV][Soul Eater]/Soul_Eater_Complete/Soul_Eater_BDBox1/SOUL_EATER_01/BDMV/STREAM/00004.m2ts')
src_f = lvf.src(r'G:/src/[BDMV][Soul Eater]/Soul_Eater_Complete/Soul_Eater_BDBox1/SOUL_EATER_01/BDMV/STREAM/00005.m2ts')

nc = lvf.src(r'G:/src/[BDMV][Soul Eater]/Soul_Eater_Complete/Soul_Eater_BDBox1/SOUL_EATER_04/BDMV/STREAM/00038.m2ts')
ncop = nc[216:2376]
nced = nc[2496:4656]

# Removing karaoke on OP/ED so I can insert my own subs
ncop_merge = ncop[:66]+src_b[57:-11]
sq_mask = kgf.squaremask(ncop_merge, ncop_merge.width, 128, 0, 866)
src_b = core.std.MaskedMerge(ncop_merge, ncop, sq_mask)

nced_cut = nced[18:2001]+src_e[1983:]
nced_mask = lvf.src(r'ed_mask.png', src=sq_mask).resize.Point(format=vs.GRAY8, matrix_s='709').std.Binarize()*2156
ed_mask = fvf.rfs(sq_mask, nced_mask, mappings="[1195 1333]")
src_e = core.std.MaskedMerge(src_e, nced_cut, ed_mask)


# This can probably be done way neater.
src = src_a+src_b+src_c+src_d+src_e+src_f
src = core.edgefixer.ContinuityFixer(src, 4, 4, 4, 4)
src_a = lvf.conditional_descale(src, height=540, b=0, c=1, w2x=True)
src_b = descale_oped(src)
src = fvf.rfs(src_a, src_b, mappings=f"[{opstart} {opstart+2159}] [{edstart} {edstart+2157}]")


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
deband = fvf.rfs(deband_a, deband_b, mappings=f"[{opstart+1233} {opstart+1353}] [{opstart+1479} {opstart+1502}] [{opstart+1807} {opstart+1851}] [{opstart+2089} {opstart+2097}] [6542 6584] [11137 11164] [20306 20393] [29819 30023] [30208 30862]")

grain = kgf.adaptive_grain(deband, 0.5, luma_scaling=4)


out = grain
final = fvf.Depth(out, 10)
final.set_output()
