from __future__ import annotations

from typing import Any, Dict, Tuple

import vapoursynth as vs
import vsencode as vse
from vardefunc import initialise_input

from project_module import flt

ini = vse.generate.init_project()

core = vse.util.get_vs_core(reserve_core=ini.reserve_core)

shader = vse.get_shader("FSRCNNX_x2_56-16-4-1.glsl")


# Sources
SRC = vse.FileInfo(f"{ini.bdmv_dir}/[BDMV][150708][Absolute Duo][Vol.04]/ABSOLUTE_DUO_VOL4/BDMV/STREAM/00005.m2ts", (24, -24))  # noqa


zones: Dict[Tuple[int, int], Dict[str, Any]] = {  # Zones for the encoder
}


@initialise_input(bits=32)
def filterchain(src: vs.VideoNode = SRC.clip_cut) -> vs.VideoNode | Tuple[vs.VideoNode, ...]:
    """Main filterchain"""
    import havsfunc as haf
    import jvsfunc as jvf
    import lvsfunc as lvf
    import vardefunc as vdf
    import vsdenoise as vsd
    from vsutil import depth

    assert src.format

    descale = lvf.scale.comparative_descale(src, kernel=lvf.kernels.Spline16())
    upscale = vdf.scale.fsrcnnx_upscale(descale, shader_file=shader, strength=85,
                                        downscaler=lvf.scale.ssim_downsample,
                                        undershoot=1.1, overshoot=1.5)
    scaled = depth(vdf.misc.merge_chroma(upscale, src), 16)

    smd = haf.SMDegrain(scaled, tr=3, thSAD=25)
    bm3d = vsd.BM3DCudaRTC(smd, sigma=[0.90, 0], refine=3).clip
    cc = jvf.ccd(bm3d, threshold=6)
    decs = vdf.noise.decsiz(cc, min_in=196 << 8, max_in=240 << 8)

    aa = lvf.aa.based_aa(decs, shader, rfactor=1.25, beta=0.6)

    deband = flt.masked_f3kdb(aa, rad=24, thr=[32, 24], grain=[24, 12])

    return deband


FILTERED = filterchain()


if __name__ == '__main__':
    vse.EncodeRunner(SRC, FILTERED).video('x264', '.settings/x264_settings', zones=zones) \
        .audio('aac').mux('LightArrowsEXE@Kaleido').run()
elif __name__ == '__vapoursynth__':
    if not isinstance(FILTERED, vs.VideoNode):
        raise vs.Error(f"Input clip has multiple output nodes ({len(FILTERED)})! Please output a single clip")
    else:
        vse.video.finalize_clip(FILTERED).set_output(0)
else:
    SRC.clip_cut.set_output(0)

    if not isinstance(FILTERED, vs.VideoNode):
        for i, clip_filtered in enumerate(FILTERED, start=1):
            clip_filtered.set_output(i)
    else:
        FILTERED.set_output(1)

    for i, audio_node in enumerate(SRC.audios_cut, start=10):
        audio_node.set_output(i)
