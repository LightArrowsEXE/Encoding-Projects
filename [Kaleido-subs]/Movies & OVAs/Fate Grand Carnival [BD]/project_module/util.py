from typing import Tuple

import vapoursynth as vs
from vardautomation import BinaryPath, VideoEncoder, VPath
from vsutil import depth, get_depth

core = vs.core


def _get_bits(clip: vs.VideoNode, expected_depth: int = 16) -> Tuple[int, vs.VideoNode]:
    """Checks bitdepth, set bitdepth if necessary, and sends original clip's bitdepth back with the clip"""
    bits = get_depth(clip)
    return bits, depth(clip, expected_depth) if bits != expected_depth else clip


def extract_frames(clip: vs.VideoNode, name: str, path: str = 'assets') -> None:
    """
    Extract all frames of a given clip to a given directory.

    Heavily based off of vardautomation's Extract function,
    but simplified to only have what I personally need here.
    """
    from lvsfunc.render import clip_async_render

    frames = clip.num_frames
    frames = range(frames)

    clip = clip.resize.Bicubic(format=vs.RGB24, matrix_in=1, dither_type='error_diffusion')
    clip = clip.std.ShufflePlanes([1, 2, 0], vs.RGB).std.AssumeFPS(fpsnum=1, fpsden=1)
    path_images = [VPath(path) / VPath((f'{name}_' + f'{f}'.zfill(len("%i" % max(frames))) + '.png')) for f in frames]

    try:
        VPath(path).mkdir(parents=True)
    except FileExistsError:
        pass

    # Frames are extracted using ffmpeg. This is much faster than using imwri
    outputs = []

    for i, path_image in enumerate(path_images):
        outputs += [
            '-compression_level', str(-1), '-pred', 'mixed',
            '-ss', f'{i}', '-t', '1', f'{path_image.to_str()}'
        ]

    settings = [
        '-hide_banner', '-loglevel', 'error', '-f', 'rawvideo',
        '-video_size', f'{clip.width}x{clip.height}',
        '-pixel_format', 'gbrp', '-framerate', str(clip.fps),
        '-i', 'pipe:', *outputs
    ]

    encoder = VideoEncoder(BinaryPath.ffmpeg, settings)

    def _cb(n: int, f: vs.VideoFrame) -> None:
        encoder.run_enc(clip, None, y4m=False)

    clip_async_render(clip, progress=f"Extracting frames to {path}...", callback=_cb)
