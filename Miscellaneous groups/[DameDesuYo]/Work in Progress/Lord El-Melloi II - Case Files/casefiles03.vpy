import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import mvsfunc as mvf
import vsTAAmbk as taa
import havsfunc as haf
core = vs.core

opstart, edstart = 2115, 30874

src_a = lvf.src(r"03/Lord El-Melloi II-sei no Jikenbo_ Rail Zeppelin Grace Note - 03 (Wakanim SC 1080p).mkv")
src_b = lvf.src(r"03/[Erai-raws] Lord El-Melloi II Sei no Jikenbo - Rail Zeppelin Grace Note - 03 [1080p][Multiple Subtitle].mkv")
src_b = src_b[0]*5+src_b[:4274]+src_b[4268]*4+src_b[4272:15466]+src_b[15466]*8+src_b[15470:]
scomp = lvf.scomp(src_a, src_b, height=480) # Matching src_a & src_b
# Double-check before- and after the CM break. Ep1 was mismatched for a frame after.

hardsubmask = kgf.hardsubmask(src_a, src_b).std.Maximum().std.Maximum()
src = core.std.MaskedMerge(src_a, src_b, hardsubmask)

src_fade = fvf.Depth(kgf.hardsubmask_fades(src_a, src_b, highpass=1300), 8)
src_fade = core.std.MaskedMerge(src_a, src_b, src_fade) # Amazon a shit
src = fvf.rfs(src, src_fade, mappings=f"[{opstart+285} {opstart+517}] [27276 27308] [25108 25179] [28316 28448]")
# Change this as much as need be every episode. Note that the original hardsubmask doesn't catch the CM break sign.

src = core.edgefixer.ContinuityFixer(src, left=1, top=1, right=1, bottom=1)

scaled = kgf.inverse_scale(src, height=720, kernel='bicubic', b=0, c=1/2, mask_detail=True)
scaled = fvf.Depth(scaled, 16)

denoise_a = mvf.BM3D(scaled, sigma=[1,0.5])
denoise_b = mvf.BM3D(scaled, sigma=[4,2])
denoise_c = mvf.BM3D(scaled, sigma=[8,4])
denoise = fvf.rfs(denoise_a, denoise_b, mappings=f"[{opstart} {opstart+284}] [{opstart+1319} {opstart+1598}] [33955 33990]")
denoise = fvf.rfs(denoise, denoise_c, mappings=f"[{opstart+875} {opstart+890}]")

aa_a = taa.TAAmbk(denoise, aatype='Nnedi3')
aa_b = taa.TAAmbk(denoise, aatype='Eedi3')
aa_c = taa.TAAmbk(denoise, aatype='Nnedi3SangNom')
aa = fvf.rfs(aa_a, aa_b, mappings=f"[{opstart+285} {opstart+517}] [{opstart+574} {opstart+621}] [{opstart+1555} {opstart+1598}] [13291 13374]")
aa = fvf.rfs(aa, aa_c, mappings=f"[{opstart+875} {opstart+890}]")

# Both bright and dark scenes are banded to hell, but since it's far less noticeable on the brighter scenes, I'm doing adaptive debanding here.
mask = kgf.adaptive_grain(scaled, show_mask=True, luma_scaling=48)
deband_a = core.f3kdb.Deband(aa, range=14, y=24, cb=16, cr=16, grainy=0, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(aa, range=17, y=32, cb=24, cr=24, grainy=12, grainc=0, output_depth=16)
merge = core.std.MaskedMerge(deband_a, deband_b, mask)


# Additional scenefiltering nonsense
deband_c = core.f3kdb.Deband(aa, range=5, y=60, cb=48, cr=48, grainy=0, grainc=0, output_depth=16)
deband_c = core.f3kdb.Deband(deband_c, range=15, y=32, cb=24, cr=24, grainy=0, grainc=0, output_depth=16)
deband_d = core.f3kdb.Deband(deband_c, range=18, y=48, cb=40, cr=40, grainy=0, grainc=0, output_depth=16)
deband_e = core.f3kdb.Deband(aa, range=19, y=48, cb=40, cr=40, grainy=0, grainc=0, output_depth=16)
deband = fvf.rfs(merge, deband_a, mappings="")
deband = fvf.rfs(deband, deband_b, mappings=f"[{opstart} {opstart+621}] [{opstart+875} {opstart+890}] [{opstart+1319} {opstart+1598}] [{edstart+465} {edstart+611}] [{edstart+1668} {edstart+1706}] [{edstart+1746} {edstart+1861}] [13375 13482] [25180 25235] [33955 33990]")
deband = fvf.rfs(deband, deband_c, mappings=f"[{opstart+757} {opstart+858}] [13291 13374] [20284 20318]")
deband = fvf.rfs(deband, deband_d, mappings="")
deband = fvf.rfs(deband, deband_e, mappings=f"[{opstart+960} {opstart+1028}] [25108 25179]")

grain_a = kgf.adaptive_grain(deband, 0.3)
grain_b = kgf.adaptive_grain(deband, 0.45, luma_scaling=1)
grain_c = kgf.adaptive_grain(deband, 1.6, static=False, luma_scaling=4)
grain = core.std.MaskedMerge(grain_a, grain_b, mask)
grain = fvf.rfs(grain, grain_b, mappings="[24841 25235] [33955 33990]")
grain = fvf.rfs(grain, grain_c, mappings=f"[{opstart} {opstart+621}] [{opstart+875} {opstart+890}] [{opstart+1029} {opstart+1095}]")


out = grain
final = fvf.Depth(out, 10)
final.set_output()
