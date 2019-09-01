import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import vsTAAmbk as taa
import mvsfunc as mvf
import havsfunc as haf
core = vs.core
core.num_threads = 4


src_a = lvf.src(r"src/Fate kaleid liner Prisma☆Illya_ Prisma☆Phantasm (Amazon VBR 1080p).mkv")[528:] # VBR
src_b = lvf.src(r"src/Fate kaleid liner Prisma☆Illya_ Prisma☆Phantasm (Amazon CBR 1080p).mkv")[528:] # CBR
src_c = lvf.src(r"src/[BDMV] 魔法少女伊莉雅/[BDMV][130927][[Fate Kaleid Liner Prisma Illya][Vol.01]/BDMV/STREAM/00007.m2ts")[13519:18039]
# Had this cut before cutting it afterwards, and too lazy to math
src_c = src_c[611]+src_c[611:693]+src_c[742:783]+src_c[807:855]+src_c[3756:3797]+src_c[3798:3911]+src_c[4447]+src_c[4447:4481]+src_c[4490:]
src_mask = kgf.adaptive_grain(src_a, show_mask=True, luma_scaling=4).std.Binarize()
src = core.std.MaskedMerge(src_a, src_b, src_mask) # Darker areas overall preserve more grain and occasionally detail in the CBR version

src = core.edgefixer.ContinuityFixer(src, left=[4,2,2], right=[3,1,1], top=1, bottom=1, radius=[8,4,4])

a, b, c = src[40895:40898], src[40898:40901], src[40901:40904]
src = kgf.insert_clip(src, c*2+b+c+b+a+b+a+b+c+a+b+a+b+a+b+c+b+a+b, 40835)
src = kgf.insert_clip(src, src[4938]*8, 4939)
src = kgf.insert_clip(src, src_c, 4947) 
src = kgf.insert_clip(src, src_c, 22569) 

src = fvf.Depth(src, 16)


scaled_a = fvf.Depth(kgf.inverse_scale(src, height=720, kernel='bicubic', b=1/3, c=1/3), 16)
scaled_b = core.resize.Spline36(src, 1280, 720, format=vs.YUV444P16) 
scaled = fvf.rfs(scaled_a, scaled_b, mappings="[2789 4946] [84698 87043]")

denoise = mvf.BM3D(scaled, sigma=[1,0.5])
darken = haf.FastLineDarkenMOD(denoise, strength=12, protection=21, luma_cap=191, threshold=4, thinning=0) # A little bit of subjective line darkening, careful not to make it too strong.
aa_a = taa.TAAmbk(darken, aatype='Eedi3', cycle=1, repair=2)
aa_b = taa.TAAmbk(darken, aatype='Nnedi3')
aa_c = taa.TAAmbk(darken, aatype='Nnedi3SangNom')
aa_d = taa.TAAmbk(darken, aatype='Eedi3SangNom', repair=2)
aa = fvf.rfs(aa_a, aa_b, mappings="[0 107]")
aa = fvf.rfs(aa, aa_c, mappings="[11376 11404]")
aa = fvf.rfs(aa, aa_d, mappings="[39196 39242] [43155 43196]")

deband_a = core.f3kdb.Deband(aa, range=5, y=0, cb=80, cr=80, grainy=0, grainc=0, output_depth=16)
deband_a = core.f3kdb.Deband(deband_a, range=15, y=40, cb=40, cr=40, grainy=0, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(aa, range=18, y=48, cb=48, cr=48, grainy=0, grainc=0, output_depth=16)
deband = fvf.rfs(deband_a, deband_b, mappings="[2789 4946]")

grain = kgf.adaptive_grain(deband, 0.3)


out = grain
final = fvf.Depth(out, 10)
final.set_output()
