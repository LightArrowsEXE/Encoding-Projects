import os
from typing import List, Tuple, Union

import vapoursynth as vs
from bvsfunc.util import ap_video_source
from lvsfunc.misc import replace_ranges, source
from lvsfunc.types import Range
from vardautomation import (JAPANESE, AudioStream, FileInfo, Mux, PresetAAC,
                            PresetBD, RunnerConfig, SelfRunner, VideoStream,
                            VPath, X265Encoder)

from fgc_filters import filters as flt

core = vs.core
core.num_threads = 16

shader = r'assets/FSRCNNX_x2_56-16-4-1.glsl'
if os.path.exists(shader) is False:
    hookpath = r"mpv/shaders/FSRCNNX_x2_56-16-4-1.glsl"
    shader = os.path.join(str(os.getenv("APPDATA")), hookpath)


# Sources
JP_BD = FileInfo(r'BDMV/BD_VIDEO/BDMV/STREAM/00004.m2ts', 24, -24,
                 idx=lambda x: source(x, force_lsmas=True, cachedir=''),
                 preset=[PresetBD, PresetAAC])
JP_BD.name_file_final = VPath(fr"premux/{JP_BD.name} (Premux).mkv")
JP_BD.a_src_cut = VPath(f"{JP_BD.name}_cut.aac")
JP_BD.do_qpfile = True


# Common variables
opstart = 0
edstart = False

# Scenefiltering
str_deband: List[Range] = [(opstart+572, opstart+590), (opstart+731, opstart+748), (opstart+1360, opstart+1379)]
aa_ranges: List[Range] = [(opstart+626, opstart+697), (opstart+824, opstart+889), (opstart+1387, opstart+1416)]
op_replace: List[int] = [opstart+857]


def main() -> Union[vs.VideoNode, Tuple[vs.VideoNode, ...]]:
    """Vapoursynth filtering"""
    import rekt
    import vardefunc as vdf
    from awsmfunc import bbmod
    from lvsfunc.mask import BoundingBox
    from vsutil import depth, get_y, insert_clip

    src = JP_BD.clip_cut

    # Fixing an animation fuck-up
    for f in op_replace:
        src = insert_clip(src, src[f], f-1)

    # Edgefixing
    ef = rekt.rektlvls(
        src, prot_val=[16, 235], min=16, max=235,
        rownum=[0, src.height-1], rowval=[16, 16],
        colnum=[0, src.width-1], colval=[16, 16],
    )

    bb_y = bbmod(ef, left=1, top=1, right=1, bottom=1, thresh=32, y=True, u=False, v=False)
    bb_uv = bbmod(bb_y, left=2, top=2, right=2, bottom=2, y=False, u=True, v=True)
    bb32, bb16 = depth(bb_uv, 32), depth(bb_uv, 16)

    # Rescaling
    l_mask = vdf.mask.FreyChen().get_mask(get_y(bb16)).morpho.Close(size=6)
    l_mask = core.std.Binarize(l_mask, 24 << 8).std.Maximum().std.Maximum()
    scaled, credit_mask = flt.rescaler(bb32, height=720, shader_file=shader)
    scaled = core.std.MaskedMerge(bb16, scaled, l_mask)
    scaled = core.std.MaskedMerge(scaled, bb16, credit_mask)

    # Denoising
    denoise = flt.multi_denoise(scaled, l_mask)

    # Anti-aliasing
    aa_clamped = flt.clamp_aa(denoise, strength=3.0)
    aa_rfs = replace_ranges(denoise, aa_clamped, aa_ranges)

    # Fix edges because they get fucked during the denoising and AA stages
    box = BoundingBox((1, 1), (src.width-2, src.height-2))
    fix_edges = core.std.MaskedMerge(scaled, aa_rfs, box.get_mask(scaled))

    # Debanding + Graining
    deband = flt.multi_debander(fix_edges, bb16)
    grain = flt.grain(deband)

    # Scenefiltering
    adap_mask = core.adg.Mask(deband.std.PlaneStats(), 10)
    deband_str = flt.placebo_debander(deband, iterations=2, threshold=6.5, radius=12, grain=4)
    grain_str = flt.grain(deband_str, strength=0.3, static=False)
    grain_str = core.std.MaskedMerge(grain, grain_str, adap_mask)

    grain = replace_ranges(grain, grain_str, str_deband)

    return grain


def output(clip: vs.VideoNode) -> vs.VideoNode:
    """Dithering down and setting TV range for the output video node"""
    from vsutil import depth

    return depth(clip, 10).std.Limiter(16 << 2, [235 << 2, 240 << 2], [0, 1, 2])

XML_TAG = "settings/tags_aac.xml"

class Encoding:
    def __init__(self, file: FileInfo, clip: vs.VideoNode) -> None:
        self.file = file
        self.clip = clip

    def run(self) -> None:
        assert self.file.a_src
        assert self.file.a_src_cut

        v_encoder = X265Encoder('settings/x265_settings_BD')

        ap_video_source(self.file.path.to_str(),
                        [self.file.frame_start, self.file.frame_end],
                        framerate=self.clip.fps,
                        noflac=True, noaac=False, nocleanup=False, silent=False)
        os.rename(self.file.path_without_ext.to_str() + "_2_cut.aac", self.file.a_src_cut.to_str())

        muxer = Mux(
            self.file,
            streams=(
                VideoStream(self.file.name_clip_output, 'HEVC BDrip by LightArrowsEXE@Kaleido', JAPANESE),
                AudioStream(self.file.a_src_cut.format(1), 'AAC 2.0', JAPANESE, XML_TAG),
                None
            )
        )

        config = RunnerConfig(v_encoder, None, None, None, None, muxer)

        runner = SelfRunner(self.clip, self.file, config)
        runner.run()
        runner.do_cleanup()


if __name__ == '__main__':
    filtered = main()
    filtered = output(filtered)  # type: ignore
    Encoding(JP_BD, filtered).run()
elif __name__ == '__vapoursynth__':
    filtered = main()
    if not isinstance(filtered, vs.VideoNode):
        raise RuntimeError("Multiple output nodes were set when `vspipe` only expected one")
    else:
        filtered.set_output(0)
else:
    JP_BD.clip_cut.set_output(0)
    FILTERED = main()
    if not isinstance(FILTERED, vs.VideoNode):
        for i, clip_filtered in enumerate(FILTERED, start=1):
            clip_filtered.set_output(i)
    else:
        FILTERED.set_output(1)
