import os
from pathlib import Path
from typing import Any, Dict, Tuple, Union

import vapoursynth as vs
from lvsfunc.misc import source
from vardautomation import FileInfo, PresetAAC, PresetWEB, VPath

from project_module import encoder as enc

core = vs.core


shader_file = 'assets/FSRCNNX_x2_56-16-4-1.glsl'
if not Path(shader_file).exists():
    hookpath = r"mpv/shaders/FSRCNNX_x2_16-0-4-1.glsl"
    shader_file = os.path.join(str(os.getenv("APPDATA")), hookpath)


# Sources
SP = FileInfo(r'src/[SubsPlease] Kimetsu no Yaiba - Yuukaku-hen - 09 (1080p) [54F873EC].mkv',  # noqa
              (864, 3021), idx=lambda x: source(x, force_lsmas=True, cachedir=''), preset=[PresetWEB, PresetAAC])
BG = FileInfo(r'src/Kimetsu no Yaiba - Yuukaku-hen - 09 - 1080p WEB H.264 -NanDesuKa (B-Global).mkv',  # noqa
              (864, 3021), idx=lambda x: source(x, force_lsmas=True, cachedir=''))
SP.name_file_final = VPath(fr"premux/{SP.name} (Premux).mkv")
SP.a_src_cut = VPath(SP.name)


zones: Dict[Tuple[int, int], Dict[str, Any]] = {  # Zones for the encoder
    (927, 1039): {'b': 0.90}
}


def filterchain() -> Union[vs.VideoNode, Tuple[vs.VideoNode, ...]]:
    """Main filterchain"""
    import debandshit as dbs
    import lvsfunc as lvf
    import vardefunc as vdf
    import adptvgrnMod as adp
    from ccd import ccd
    from vsutil import depth, get_w, get_y, iterate, Range

    src = SP.clip_cut
    src = depth(src, 32)
    src_y = get_y(src)

    # Descaling + Credit mask. We're also deblocking while descaled for speed/memory purposes
    descale = lvf.kernels.Catrom().descale(src_y, get_w(855), 855)
    upscale = lvf.kernels.Catrom().scale(descale, src.width, src.height)

    # Deblocking
    debl = lvf.deblock.vsdpir(descale, strength=6.5, matrix=1)

    # Rescaling
    rescale = vdf.scale.nnedi3_upscale(debl, use_znedi=True)
    dnscale = lvf.scale.ssim_downsample(rescale, src.width, src.height)
    scaled = depth(vdf.misc.merge_chroma(dnscale, src), 16)

    credit_mask = lvf.scale.descale_detail_mask(src_y, upscale, threshold=0.052)
    credit_mask = iterate(credit_mask, core.std.Inflate, 2)
    credit_mask = iterate(credit_mask, core.std.Maximum, 2)
    credit_mask = depth(credit_mask, 16, range_in=Range.FULL, range=Range.LIMITED)

    # Denoising
    den_uv = ccd(scaled, threshold=5.5, matrix='709')
    decs = vdf.noise.decsiz(den_uv, sigmaS=6.0, min_in=200 << 8, max_in=236 << 8)

    # Debanding
    deband = dbs.dumb3kdb(decs, radius=18, threshold=[32, 28], grain=[24, 12])

    # Merge credits back in. Credits are also denoised because of ugly compression
    credit_cleaned = core.dfttest.DFTTest(depth(src, 16), sigma=12.0)
    creds = core.std.MaskedMerge(deband, credit_cleaned, credit_mask)

    # Graining
    grain = adp.adptvgrnMod(creds, strength=0.15, sharp=80, luma_scaling=8, grain_chroma=False)
    grain_str = adp.adptvgrnMod(creds, strength=1.0, sharp=150, luma_scaling=1, grain_chroma=False)
    grain = lvf.rfs(grain, grain_str, [(927, 1039)])

    return grain


if __name__ == '__main__':
    FILTERED = filterchain()
    enc.Encoder(SP, FILTERED).run(zones=zones, alt_src=BG)  # type: ignore
elif __name__ == '__vapoursynth__':
    FILTERED = filterchain()
    if not isinstance(FILTERED, vs.VideoNode):
        raise ImportError(f"Input clip has multiple output nodes ({len(FILTERED)})! Please output just 1 clip")
    else:
        enc.dither_down(FILTERED).set_output(0)
else:
    SP.clip_cut.std.SetFrameProp('node', intval=0).text.Text('src').set_output(0)
    FILTERED = filterchain()
    if not isinstance(FILTERED, vs.VideoNode):
        for i, clip_filtered in enumerate(FILTERED, start=1):
            clip_filtered.std.SetFrameProp('node', intval=i).set_output(i)
    else:
        FILTERED.std.SetFrameProp('node', intval=1).set_output(1)
