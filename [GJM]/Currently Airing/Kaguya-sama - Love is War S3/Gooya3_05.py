import multiprocessing as mp
from typing import Any, Dict, List, Tuple, Union

import vapoursynth as vs
from glob import glob
import yaml
import ntpath
from lvsfunc.misc import source
from lvsfunc.types import Range
from vardautomation import FileInfo, PresetBD, VPath, get_vs_core
from vardefunc import initialise_input

from project_module import encoder as enc
from project_module import flt

with open("config.yaml", 'r') as conf:
    config = yaml.load(conf, Loader=yaml.FullLoader)

core = get_vs_core(range(0, (mp.cpu_count() - 2)) if config['reserve_core'] else None)


# Sources
SRC_DIR = config["bdmv_dir"]
JP_WEB = FileInfo(f"{glob(f'{SRC_DIR}/*{ntpath.basename(__file__)[-5:-3]}*.mkv')[0]}",
                  idx=lambda x: source(x, force_lsmas=True, cachedir=''), preset=[PresetBD])
JP_NCED = None
JP_WEB.name_file_final = VPath(fr"premux/{JP_WEB.name} (Premux).mkv")
JP_WEB.a_src_cut = VPath(JP_WEB.name)


# OP/ED scenefiltering
opstart = False
edstart = False
op_offset = 1
ed_offset = 1


# Freezeframing
ff_first: List[int] = [
]

ff_last: List[int] = [
]

ff_repl: List[int] = [
]

deblock_ranges: List[Range] = [
]

zones: Dict[Tuple[int, int], Dict[str, Any]] = {  # Zones for the encoder
    (32052, 32129): {'b': 0.90}
}


for k, v in zones:
    deblock_ranges += [(k, v)]

# Adding zones that shouldn't be deblocked
zones |= {
    (32370, 34528): {'b': 1.15}
}

run_script: bool = __name__ == '__main__'


@initialise_input(bits=32)
def filterchain(src: vs.VideoNode = JP_WEB.clip_cut) -> Union[vs.VideoNode, Tuple[vs.VideoNode, ...]]:
    """Main filterchain"""
    import havsfunc as haf
    import lvsfunc as lvf
    import vardefunc as vdf
    import vsdenoise as vsd
    from ccd import ccd
    from finedehalo import fine_dehalo
    from vsmlrt import Backend
    from vsutil import depth, get_w, get_y, iterate

    assert src.format

    src_y = get_y(src)

    # Descaling and rescaling
    l_mask = vdf.mask.FDOG().get_mask(src_y, lthr=0.125, hthr=0.027).rgsf.RemoveGrain(4).rgsf.RemoveGrain(4)
    l_mask = l_mask.std.Minimum().std.Deflate().std.Median().std.Convolution([1] * 9)
    sq_mask = lvf.mask.BoundingBox((4, 4), (src.width-4, src.height-4)).get_mask(src_y).std.Invert()

    # Probably incorrect, but the results seem to be good enough and credit mask catches very little.
    # I don't see any obvious lancsoz ringing either. The fuck did they do to this?
    descale = lvf.kernels.Catrom().descale(src_y, get_w(874), 874)
    upscale = lvf.kernels.Catrom().scale(descale, src.width, src.height)

    credit_mask = lvf.scale.descale_detail_mask(src_y, upscale, threshold=0.075)
    credit_mask = iterate(credit_mask, core.std.Inflate, 2)
    credit_mask = iterate(credit_mask, core.std.Maximum, 2)
    credit_mask = core.std.Expr([credit_mask, sq_mask], "x y -").std.Limiter()

    upscaled = vdf.scale.nnedi3_upscale(descale, use_znedi=True, pscrn=1)
    downscale = lvf.scale.ssim_downsample(upscaled, src.width, src.height)
    downscale = core.std.MaskedMerge(downscale, src_y, credit_mask)
    scaled = depth(vdf.misc.merge_chroma(downscale, src), 16)

    smd = haf.SMDegrain(scaled, tr=3, thSAD=50)
    dft = smd.dfttest.DFTTest(sigma=4)
    bm3d = vsd.BM3DCudaRTC(smd, ref=dft, sigma=[0.75, 0.0]).clip
    den_uv = ccd(bm3d, threshold=7.5)

    debl = lvf.deblock.vsdpir(den_uv, strength=75, tiles=8,
                              backend=Backend.TRT(fp16=True) if run_script
                              else Backend.ORT_CUDA(fp16=True))
    darken = haf.FastLineDarkenMOD(debl, strength=20)
    debl = lvf.rfs(den_uv, darken, deblock_ranges)

    decs = vdf.noise.decsiz(debl, min_in=200 << 8, max_in=240 << 8)

    dering = haf.HQDeringmod(decs, mthr=40, nrmode=2, sharp=0, darkthr=0)
    dehaloa = haf.FineDehalo(decs, rx=1.85, ry=1.85, thma=164, darkstr=0)
    dehalo = core.std.Expr([decs, dering, dehaloa], "x y - abs x z - abs < y z ?")
    dehalo = fine_dehalo(decs, dehalo)

    if ff_first:
        dehalo = dehalo.std.FreezeFrames(ff_first, ff_last, ff_repl)

    detail_mask = lvf.mask.detail_mask(dehalo, rad=4, brz_a=0.015, brz_b=0.05)
    deband = core.std.MaskedMerge(core.average.Mean([
        flt.masked_f3kdb(dehalo, rad=17, thr=24, grain=[12, 6]),
        flt.masked_f3kdb(dehalo, rad=21, thr=[32, 24], grain=[24, 12]),
        flt.masked_placebo(dehalo, rad=10, thr=3.5, grain=4)
    ]), dehalo, detail_mask)

    grain = vdf.noise.Graigasm(
        thrs=[x << 8 for x in (32, 80, 128, 176)],
        strengths=[(0.125, 0.0), (0.10, 0.0), (0.05, 0.0), (0.0, 0.0)],
        sizes=(1.0, 1.0, 1.0, 1.0),
        sharps=(80, 65, 50, 50),
        grainers=[
            vdf.noise.AddGrain(seed=69420, constant=True),
            vdf.noise.AddGrain(seed=69420, constant=True),
            vdf.noise.AddGrain(seed=69420, constant=True)
        ]).graining(deband)

    return grain


if __name__ == '__main__':
    FILTERED = filterchain()
    enc.Encoder(JP_WEB, FILTERED).run(zones=zones)  # type: ignore
elif __name__ == '__vapoursynth__':
    FILTERED = filterchain()
    if not isinstance(FILTERED, vs.VideoNode):
        raise ImportError(f"Input clip has multiple output nodes ({len(FILTERED)})! Please output just 1 clip")
    else:
        enc.dither_down(FILTERED).set_output(0)
else:
    JP_WEB.clip_cut.std.SetFrameProp('node', intval=0).set_output(0)
    FILTERED = filterchain()
    if not isinstance(FILTERED, vs.VideoNode):
        for i, clip_filtered in enumerate(FILTERED, start=1):
            clip_filtered.std.SetFrameProp('node', intval=i).set_output(i)
    else:
        FILTERED.std.SetFrameProp('node', intval=1).set_output(1)
