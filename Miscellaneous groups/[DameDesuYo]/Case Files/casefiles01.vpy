import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import mvsfunc as mvf
import vsTAAmbk as taa
import havsfunc as haf
core = vs.core


src_a = lvf.src(r"01/Lord El-Melloi II-sei no Jikenbo_ Rail Zeppelin Grace Note - 01 (Wakanim SC 1080p) [!].mkv")
src_b = lvf.src(r"01/[Erai-raws] Lord El-Melloi II Sei no Jikenbo - Rail Zeppelin Grace Note - 01 [1080p][Multiple Subtitle].mkv")
src_a = src_a[1:15799]+src_a[15798]+src_a[15799:]
scomp = lvf.scomp(src_a, src_b, height=480) # Matching src_a & src_b
# Double-check before- and after the CM break. Ep1 was mismatched for a frame after.

hardsubmask = kgf.hardsubmask(src_a, src_b).std.Maximum().std.Maximum()
src = core.std.MaskedMerge(src_a, src_b, hardsubmask)

src_fade = fvf.Depth(kgf.hardsubmask_fades(src_a, src_b, highpass=1300), 8)
src_fade = core.std.MaskedMerge(src_a, src_b, src_fade) # Amazon a shit
src = fvf.rfs(src, src_fade, mappings="[0 120] [857 1008] [3392 3535] [4034 4153] [4425 4511] [11007 11375] [11541 11610] [15728 15799] [15986 16153] [22892 23057] [32686 32805] [33974 34090]")
# Change this as much as need be every episode. Note that the original hardsubmask doesn't catch the CM break sign.

src = core.edgefixer.ContinuityFixer(src, left=[2,1,1], top=1, right=1, bottom=1)

scaled = kgf.inverse_scale(src, height=720, kernel='bicubic', b=0, c=1/2, mask_detail=True)
scaled = fvf.Depth(scaled, 16)

denoise = mvf.BM3D(scaled, sigma=[1,0.5])
aa = taa.TAAmbk(denoise, aatype='Nnedi3')

# Both bright and dark scenes are banded to hell, but since it's far less noticeable on the brighter scenes, I'm doing adaptive debanding here.
mask = kgf.adaptive_grain(scaled, show_mask=True, luma_scaling=48)
deband_a = core.f3kdb.Deband(aa, range=14, y=24, cb=16, cr=16, grainy=0, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(aa, range=17, y=32, cb=24, cr=24, grainy=12, grainc=0, output_depth=16)
merge = core.std.MaskedMerge(deband_a, deband_b, mask)


# Additional scenefiltering nonsense
deband_c = core.f3kdb.Deband(aa, range=5, y=60, cb=48, cr=48, grainy=0, grainc=0, output_depth=16)
deband_c = core.f3kdb.Deband(deband_c, range=15, y=32, cb=24, cr=24, grainy=0, grainc=0, output_depth=16)
deband_d = core.f3kdb.Deband(deband_c, range=18, y=48, cb=40, cr=40, grainy=0, grainc=0, output_depth=16)
deband = fvf.rfs(merge, deband_a, mappings="[14421 14541]")
deband = fvf.rfs(deband, deband_b, mappings="[14239 14367] [20918 21234] [21427 22111] [22183 23057] [31960 32637]")
deband = fvf.rfs(deband, deband_c, mappings="[1009 1057]")
deband = fvf.rfs(deband, deband_d, mappings="[22112 22182]")

grain_a = kgf.adaptive_grain(deband, 0.3)
grain_b = kgf.adaptive_grain(deband, 0.45)
sf_merge = core.std.MaskedMerge(grain_a, grain_b, mask)
sf_merge = fvf.rfs(sf_merge, grain_b, mappings="[22112 22182] [31960 32637]")


out = sf_merge # merge for standard filterchain, sf_merge for scenefiltered filterchain
final = fvf.Depth(out, 10)
final.set_output()
