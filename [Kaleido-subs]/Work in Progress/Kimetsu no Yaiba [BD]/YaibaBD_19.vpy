import vapoursynth as vs
import fvsfunc as fvf
import kagefunc as kgf
import lvsfunc as lvf
import mvsfunc as mvf
import havsfunc as haf
from cooldegrain import *
from knnfunc import *
from nnedi3_rpow2 import *
from vsutil import *
core = vs.core

opstart = 2805-2159

# There are some frames with stylized dark background and slow-motion effects.
# They be will filtered slightly stronger than other scenes, and heavily grained because I like the look.
darker_shots = """
               [26 37]
               [15897 16401]
               [23301 23322]
               [25737 25778]
               [29029 29058]
               [29298 30017]
               """


src = lvf.src(r"BDMV/[BDMV][200220][Kimetsu no Yaiba][Vol.8]/BDMV/STREAM/00005.m2ts")
src = src[:-25]
src = fvf.Depth(src, 16)


b, c = 1/5, 2/5
y, u, v = split(src)
# Descaling & create credit mask
descaled = core.descale.Debicubic(fvf.Depth(y, 32), get_w(855), 855, b, c)
upscaled = core.resize.Bicubic(descaled, y.width, y.height, filter_param_a=b, filter_param_b=c)
#credit_mask = core.std.Expr([fvf.Depth(y, 32), upscaled], 'x y - abs').std.Binarize(0.05)
credit_mask = core.std.Expr([fvf.Depth(y, 32), upscaled], "x y - abs 0.015 < 0 1 ?").std.Maximum().std.Maximum().std.Inflate().std.Inflate()

# waifu2x to fix up two frames in the OP with very bad noise
w2x = mvf.ToYUV(core.w2xc.Waifu2x(mvf.ToRGB(descaled), noise=1, scale=1, gpu=0)).resize.Point(format=descaled.format)
w2x = fvf.rfs(descaled, w2x, mappings=f"{opstart+1593} {opstart+1594}")

# Fairly weak denoising. Stronger denoising on brighter areas of a frame.
# Done while descaled because it's overall faster *and* more effective.
d_mask = kgf.adaptive_grain(fvf.Depth(descaled, 16), show_mask=True, luma_scaling=8)
denoise_a = CoolDegrain(w2x, tr=1, thsad=72, thsadc=48, bits=16, blksize=8, overlap=4)
denoise_b = CoolDegrain(w2x, tr=1, thsad=24, thsadc=48, bits=16, blksize=8, overlap=4)
denoise = core.std.MaskedMerge(denoise_a, denoise_b, d_mask)
denoise = fvf.rfs(denoise, denoise_a, mappings=f"""[{opstart+28} {opstart+288}] [{opstart+401} {opstart+406}] [{opstart+1310} {opstart+1398}]
                                                   """)

# Some AA to fix up instances of bad lineart.
# Done while descaled for similar reasons as L37
aa_a = lvf.upscaled_sraa(denoise, rep=2)
aa_b = knnAA(denoise)
aa = fvf.rfs(denoise, aa_a, mappings=f"""[{opstart+1017} {opstart+1079}] [{opstart+1312} {opstart+1368}] {opstart+1593} {opstart+1594} [{opstart+1895} {opstart+2003}]
                                         [7432 7515] [8598 8634] [8729 8756] [9135 9266] [9315 9464] [9549 9575]
                                         [10196 10255] [11382 11457] [17740 17791] [18102 18213] [18316 18358]
                                         [18409 18429] [18480 18521] [18608 18655] [18704 18895] [19479 19602]
                                         [21861 21976] [22055 22096] [22173 22358] [22509 22580] [22731 22928]
                                         [23210 23300] [23586 23645] [24082 24271] [24368 24409] [27915 27997]
                                         [28044 28062] [28101 28392] [28498 28578] [28714 28715] [28760 28778]
                                         [28827 28849] [28872 28875] [28910 28925] [29161 29179] [29502 29651]
                                         [29934 30017] [30027 30077] [30132 30207]""")
aa = fvf.rfs(aa, aa_b, mappings=darker_shots + "")

# Upscaling and applying credit mask to OP and ED
upscaled = nnedi3_rpow2(aa).resize.Bicubic(src.width, src.height)
upscaled = join([upscaled, u, v])
m_upscaled = core.std.MaskedMerge(upscaled, src, fvf.Depth(credit_mask, 16))
scaled = fvf.rfs(upscaled, m_upscaled, mappings=f"[{opstart} {opstart+2159}]")
scaled = fvf.rfs(scaled, src, mappings="[30930 33086]")


# Much like the denoising, way stronger debanding is performed on brighter areas.
# This way less perceivable detail is lost to the void. Darker areas will be grained stronger instead.
deb_d_mask = fvf.Depth(kgf.adaptive_grain(src, show_mask=True, luma_scaling=8), 16)
deband_a = core.f3kdb.Deband(scaled, range=21, y=56, cb=48, cr=48, grainy=12, grainc=0, output_depth=16)
deband_b = core.f3kdb.Deband(scaled, range=17, y=40, cb=32, cr=32, grainy=24, grainc=0, output_depth=16)
deband = core.std.MaskedMerge(deband_a, deband_b, deb_d_mask)
deband = fvf.rfs(deband, deband_a, mappings=darker_shots +
                                            f"""[{opstart+2004} {opstart+2046}] [{opstart+2113} {opstart+2156}]
                                                [2806 2949] [3030 3113] [3630 3673] [3746 3873] [4056 4231] 
                                                [6734 6829] [7516 7773] [10256 10473] [11086 11174] [11554 11616] 
                                                [13451 13522] [13955 14056] [15549 15704] [16993 17070] 
                                                [17305 17514] [20798 20869] [20950 21015] [21388 21561]
                                                [22983 23112] [23173 23209] [24688 24761] [25711 25736]
                                                [25779 25922] [26441 26700] [27333 27560] [27665 27748]
                                                [28026 28170] [28579 28778] [28827 29028] [30018 30388]
                                                [30423 30771] [30822 30929]""")

# Graining. Strong dynamic grain added to parts of the OP and darker slow-motion scenes.
grain_a = kgf.adaptive_grain(deband, 0.3, luma_scaling=8)
grain_b = kgf.adaptive_grain(deband, 1)
grain_c = core.grain.Add(deband, var=6, uvar=0, constant=False)
grain_d = core.grain.Add(deband, var=3, uvar=0, constant=False)
grain = fvf.rfs(grain_a, grain_b, mappings=f"""[{opstart+1128} {opstart+1296}] [{opstart+2004} {opstart+2046}] [{opstart+2113} {opstart+2156}]
                                               [38 59] [8347 8451] [11554 11616] [20798 20869] [20950 21015]
                                               [21388 21860] [23173 23209] [23323 23366] [23394 23645] 
                                               [23978 24009] [24234 24271] [24368 24761] [26441 26700]
                                               [26869 27032] [27333 27560] [27665 27748] [27815 28392] 
                                               [28827 29028] [29059 29118] [30018 30929]""")
grain = fvf.rfs(grain, grain_c, mappings=f"[{opstart+28} {opstart+288}] [{opstart+401} {opstart+406}] [{opstart+1313} {opstart+1368}]")
grain = fvf.rfs(grain, grain_d, mappings=darker_shots + "[25714 25736] [25779 25922] [26076 26440] [26701 26868]")


out = grain
final = fvf.Depth(out, 10)
final.set_output()
