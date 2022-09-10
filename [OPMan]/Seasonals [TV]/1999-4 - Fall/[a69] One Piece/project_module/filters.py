from pathlib import Path

import vapoursynth as vs  # noqa
import vardefunc as vdf
from vskernels import Catrom
from vsscale import GenericScaler, ssim_downsample

core = vs.core

__all__: list[str] = [
    'NoShiftCatrom',
    'shader_scaler',
]


def shader_scaler(shader: str | Path, strength: float) -> GenericScaler:
    return GenericScaler(
        vdf.scale.fsrcnnx_upscale, shader_file=shader, downscaler=ssim_downsample,
        overshoot=1.5, undershoot=1.5, profile='slow', strength=strength
    )


class NoShiftCatrom(Catrom):
    def shift(self, clip, *args, **kwargs):
        return clip
