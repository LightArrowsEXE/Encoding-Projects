from typing import Tuple
import lvsfunc as lvf

import vapoursynth as vs


def _get_bits(clip: vs.VideoNode, expected_depth: int = 16) -> Tuple[int, vs.VideoNode]:
    """Checks bitdepth, set bitdepth if necessary, and sends original clip's bitdepth back with the clip"""
    from vsutil import depth, get_depth

    bits = get_depth(clip)
    return bits, depth(clip, expected_depth) if bits != expected_depth else clip


def gen_kf(clip: vs.VideoNode, kf_path: str):
    scenes = lvf.render.find_scene_changes(clip, lvf.render.SceneChangeMode.WWXD_SCXVID_UNION)
    with kf_path.open('w', encoding='utf-8') as f:
        f.writelines(f'{s} K\n' for s in scenes)
