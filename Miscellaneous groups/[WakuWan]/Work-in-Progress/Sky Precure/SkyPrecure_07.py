from typing import Any, cast
from pathlib import Path

import vsencode as vse
from vstools import core, finalize_clip, vs  # noqa type:ignore

core.set_affinity()

ini = vse.generate.init_project('x265')
run = __name__ in ('__vapoursynth__', '__main__')
ep_num = Path(__file__).stem.split("_")[-1]

# Sources
SRC = vse.FileInfo(
    list(Path('src/').glob(f'[*- {ep_num}*.mkv.dgi'))[0], [(252, -48)], idx=core.dgdecodenv.DGSource
)

A_SRC = vse.FileInfo(
    list(Path('src/').glob(f'soaring*{ep_num}*.mkv'))[0], [(360, None)]
)

# Uncomment if audio source is late.
# A_SRC = vse.FileInfo(
#     list(Path('src/').glob(f'[*- {ep_num}*.mkv'))[0], [(252, -48)]
# )

# Zoning for x265.
zones: dict[tuple[int, int], dict[str, Any]] = {}


# Filterchain.
def filterchain(clip: vs.VideoNode, draft: bool = False) -> vs.VideoNode | tuple[vs.VideoNode, ...]:
    import lvsfunc as lvf  # noqa type:ignore
    from vstools import insert_clip, replace_ranges  # noqa type:ignore

    from project import filtering

    assert clip.format

    if draft:
        return clip

    return filtering(clip, draft)

if __name__ == "__main__":
    runner = vse.EncodeRunner(SRC, cast(vs.VideoNode, filterchain(SRC.clip_cut)))
    runner.video(zones=zones)

    # Replacing with better audio source. Re-encode doesn't impact quality because >V 127
    runner.audio(
        external_audio_clip=A_SRC.clip, external_audio_file=A_SRC.path.to_str(),
        custom_trims=A_SRC.trims_or_dfs
    )

    runner.mux('LightarrowsEXE@Kaleido')
    runner.run(False)
elif __name__ == "__vapoursynth__":
    FILTERED = filterchain(SRC.clip_cut)

    if not isinstance(FILTERED, vs.VideoNode):
        raise vs.Error(f"Input clip has multiple output nodes ({len(FILTERED)})! "
                       "Please output a single clip")
    else:
        finalize_clip(cast(vs.VideoNode, FILTERED)).set_output(0)
else:
    SRC.clip_cut.std.SetFrameProps(Name="CR").set_output(0)

    FILTERED = filterchain(SRC.clip_cut)

    if not isinstance(FILTERED, vs.VideoNode):
        for i, flt in enumerate(cast(tuple, FILTERED), start=1):
            cast(vs.VideoNode, flt).set_output(i)
    else:
        cast(vs.VideoNode, FILTERED).set_output(1)

    # for i, audio_node in enumerate(DVD.audios_cut, start=10):
    #     audio_node.set_output(i)
