import mimetypes
import os
from glob import glob
from pathlib import Path


__all__: list[str] = [
    'get_audio_paths',
]


def get_audio_paths(path: str, return_glob: bool = False) -> list[Path]:
    """
    Find the audio files based on the path of the index file.

    I should really just build this straight into `lvsfunc.source` sometime, tbh.
    Or get vsencode to do it.

    :param path:            Path to index(ed) file.
    :param return_glob:     Return the glob list instead of a list of filtered paths.
                            This is only useful if the mimetype detection fails for whatever reason.

    :return:                List of all audio files found or a glob list containing every match.
    """
    rel_path = Path(os.path.relpath(path))

    audio_glob = glob(rel_path.stem + "*.w*", root_dir=rel_path.parents[0])

    if return_glob:
        return [rel_path.parents[0] / Path(path) for path in audio_glob]

    audio_paths: list[Path] = []

    for f in audio_glob:
        print(mimetypes.types_map.get(str(rel_path.parents[0] / Path(f))))
        if mimetypes.types_map.get(os.path.splitext(f)[-1], "").startswith("audio/"):
            audio_paths += [rel_path.parents[0] / Path(f)]

    return audio_paths
