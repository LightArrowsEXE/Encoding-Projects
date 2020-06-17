import kagefunc as kgf
import lvsfunc as lvf
import xvs
from vsutil import depth, join, plane

import vapoursynth as vs

core                = vs.core
core.max_cache_size = 1024 * 4
core.num_threads    = 14


# First black frame of both OP and ED
opstart = None
edstart = 0


# Arguments for debanding, upscaling, etc.
deband_args = dict(iterations = 2, threshold = 6, radius = 14)


src = lvf.src(r'BDMV/Fate Extra Last Encore/Vol5/BDROM/BDMV/STREAM/00008.m2ts')[24:-24]
src = core.std.Limiter(depth(src, 32), min=0, max=1, planes=0)


# Warping appears to fix up the starved chroma fairly well, so that's what we're doing here
l_mask = lvf.util.quick_resample(src, kgf.retinex_edgemask)
cwarp = core.std.MaskedMerge(xvs.WarpFixChromaBlend(src, depth=6), src, l_mask)
cwarp = core.rgsf.Repair(cwarp, src, 13)


detail_mask = lvf.denoise.detail_mask(cwarp, rad=3, radc=4, brz_a=0.03, brz_b=0.025)
deband = join([ # Don't ask me why, but for some godforsaken reason, this is twice as fast to process
                core.placebo.Deband(plane(cwarp, 0), grain = 6, **deband_args),
                core.placebo.Deband(plane(cwarp, 1), grain = 0, **deband_args),
                core.placebo.Deband(plane(cwarp, 2), grain = 0, **deband_args)
])
deband = core.std.MaskedMerge(deband, cwarp, detail_mask)

grain = kgf.adaptive_grain(deband, 0.15)


out = grain
final = depth(out, 10)
final.set_output()
