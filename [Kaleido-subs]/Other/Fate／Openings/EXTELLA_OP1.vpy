import vapoursynth as vs
import debandshit as ds
import fvsfunc as fvf
import havsfunc as haf
import kagefunc as kgf
import lvsfunc as lvf
from vsTAAmbk import TAAmbk
from functools import partial
core = vs.core


blends_a = range(2, 3030, 5)
blends_b = range(3, 3030, 5)
expr = ["z a 2 / - y x 2 / - +"]


def deblend(n, clip):
    # Thanks Myaa, motbob and kageru!
    if n%5 in [0, 1, 4]:
        return clip
    else:
        if n in blends_a:
            c, cd, da, a = clip[n-1], clip[n], clip[n+1], clip[n+2]
            return core.std.Expr([c, cd, da, a], expr)
        else:
            return clip


src = lvf.src(r'src/VIDEO_OPENING_jp_40534656.mkv')
src = fvf.AutoDeblock(src)


scaled_a = kgf.inverse_scale(src, height=810, 
                           kernel='bicubic', b=0, c=1/2,
                           denoise=True, use_gpu=True, 
                           bm3d_sigma=2.5).resize.Point(
                           src_left=-0.25) # damnit kageru
scaled_b = kgf.inverse_scale(src, height=810, 
                           kernel='bicubic', b=0, c=1/2).resize.Point(
                           src_left=-0.25)
scaled = fvf.rfs(scaled_a, scaled_b, mappings="[1310 1394]")
scaled = fvf.Depth(scaled, 16)

deblend = core.std.FrameEval(scaled, partial(deblend, clip=scaled))
deblend = core.std.DeleteFrames(deblend, blends_b).std.AssumeFPS(fpsnum=24000, fpsden=1001)


# OP is pretty blurry, even after being descaled. Doing some sharpening to combat this, but also have to make sure not to ring the shit out of it
aa = TAAmbk(deblend, aatype='Eedi3', sharp=120, repair=2)
aa = haf.HQDeringmod(aa, nrmode=2, darkthr=0, sharp=0, mthr=56)

# Half of this shit is usually overkill, but at this point I really don't care
d_mask = kgf.adaptive_grain(deblend, show_mask=True, luma_scaling=2)
deband_a = core.f3kdb.Deband(aa, range=16, y=32, cb=24, cr=24, grainy=36, grainc=0, output_depth=16)
deband_b = ds.f3kbilateral(aa, range=21, y=96, c=88) # was considering limiting this, but the banding comes back. :'<
deband_c = core.f3kdb.Deband(aa, range=18, y=48, cb=48, cr=48, grainy=72, grainc=0, dynamic_grain=True, output_depth=16)
deband = fvf.rfs(deband_a, deband_b, mappings="[466 599] [803 821]")
deband = fvf.rfs(deband, deband_c, mappings="[0 213] [1027 1233] [1410 1954]")

# This OP looks bad, and is mostly destroyed now. Might as well grain the shit out of it, since at least the grain does a good job of hiding my failures.
grain_a = kgf.adaptive_grain(deband, 0.8, luma_scaling=6)
grain_b = kgf.adaptive_grain(deband, 1.4, luma_scaling=2)
grain_c = kgf.adaptive_grain(deband, 1, luma_scaling=12)
grain_d = kgf.adaptive_grain(deband, 2.5, luma_scaling=12, static=False)
grain = fvf.rfs(grain_a, grain_b, mappings="[466 599] [803 821]")
grain = fvf.rfs(grain, grain_c, mappings="[1027 1233] [1410 1954]")
grain = fvf.rfs(grain, grain_d, mappings="[0 213]")


out = grain
final = fvf.Depth(out, 10)
final.set_output()
