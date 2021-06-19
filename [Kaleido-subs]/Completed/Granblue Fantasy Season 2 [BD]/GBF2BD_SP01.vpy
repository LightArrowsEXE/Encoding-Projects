import lvsfunc as lvf
import vapoursynth as vs
from adptvgrnMod import adptvgrnMod
from vsutil import depth

from gbf2_filters_common import filters

core = vs.core


src = lvf.src(r"BDMV/GRANBLUE_FANTASY_SEASON2_7/BDMV/STREAM/00001.m2ts", cachedir="")[:-27]
src = depth(src, 16)

scaled, credit_mask = filters.rescaler(src, height=844)
denoise = filters.denoising(scaled)
aa_clamped = filters.antialiasing(denoise)

credits_merged = core.std.MaskedMerge(aa_clamped, depth(src, 16), credit_mask)

deband = filters.debanding(credits_merged)
grain = adptvgrnMod(deband, strength=0.3, luma_scaling=10, size=1.25, sharp=80, grain_chroma=False, seed=42069)


final = depth(grain, 10)
final.set_output(0)


if __name__ == '__vapoursynth__':
    import os
    from pathlib import Path

    from lvsfunc.render import SceneChangeMode, find_scene_changes


    out_path = Path(f'{Path.cwd()}/.qp/{os.path.basename(__file__)[:-4]}_qpfile.txt')
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if os.path.isfile(out_path) is False:
        with open(out_path, 'w') as o:
            for f in find_scene_changes(src, SceneChangeMode.WWXD_SCXVID_UNION):
                o.write(f"{f} I -1\n")
