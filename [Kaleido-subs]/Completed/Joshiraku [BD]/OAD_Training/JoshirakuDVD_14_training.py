import os
import random
import subprocess
from pathlib import Path
from typing import BinaryIO, List, NamedTuple, Set, Tuple, cast

import vapoursynth as vs
from lvsfunc.misc import source
from lvsfunc.progress import (BarColumn, FPSColumn, Progress, TextColumn,
                              TimeRemainingColumn)
from lvsfunc.render import clip_async_render

core = vs.core


class ClipForDatasets(NamedTuple):  # noqa: PLC0115
    clip: vs.VideoNode
    res_type: str


class Datasets(NamedTuple):  # noqa: PLC0115
    hr: ClipForDatasets
    lr: ClipForDatasets


# Source files
JP_DVD_clips: List[vs.VideoNode] = [
    source(r'../DVDISO/JOSHIRAKU_01.d2v', rff=False)[4844:74402],
    source(r'../DVDISO/JOSHIRAKU_02.d2v', rff=False)[4844:74398],
    source(r'../DVDISO/JOSHIRAKU_03.d2v', rff=False)[4844:74400],
    source(r'../DVDISO/JOSHIRAKU_04.d2v', rff=False)[4844:74399],
    source(r'../DVDISO/JOSHIRAKU_05.d2v', rff=False)[4844:74401],
    source(r'../DVDISO/JOSHIRAKU_06.d2v', rff=False)[19245:122872]
]

JP_BD_clips: List[vs.VideoNode] = [
    source(r'../BDMV/120926_JOSHIRAKU_VOL1/BDMV/STREAM/00000.m2ts')[24:-42],
    source(r'../BDMV/121024_JOSHIRAKU_VOL2/BDMV/STREAM/00000.m2ts')[24:-46],
    source(r'../BDMV/121128_JOSHIRAKU_VOL3/BDMV/STREAM/00000.m2ts')[24:-44],
    source(r'../BDMV/130123_JOSHIRAKU_VOL4/BDMV/STREAM/00000.m2ts')[24:-45],
    source(r'../BDMV/130227_JOSHIRAKU_VOL5/BDMV/STREAM/00000.m2ts')[24:-43],
    source(r'../BDMV/130522_JOSHIRAKU_VOL6/BDMV/STREAM/00000.m2ts')[24:-29],
]

PROPS_DVD: Set[Tuple[str, int]] = {
    ('_ChromaLocation', 0),
    ('_Matrix', 6),
    ('_Transfer', 6),
    ('_Primaries', 6),
    ('_FieldBased', 0)
}

PROPS_BD: Set[Tuple[str, int]] = {
    ('_Matrix', 1),
    ('_Transfer', 1),
    ('_Primaries', 1)
}

# Prepare for encoding
dvd_full = core.std.BlankClip(JP_DVD_clips[0][0])
bd_full = core.std.BlankClip(JP_BD_clips[0][0])

for c in JP_DVD_clips:
    dvd_full += c

for c in JP_BD_clips:
    bd_full += c

dvd_full = dvd_full[1:].std.AssumeFPS(fpsnum=24000, fpsden=1001)
bd_full = bd_full[1:]

for prop, val in PROPS_DVD:
    dvd_full = dvd_full.std.SetFrameProp(prop, intval=val)

for prop, val in PROPS_BD:
    bd_full = bd_full.std.SetFrameProp(prop, intval=val)


PATH_DATASET = Path('dataset')
PATH_DATASET_TRAIN = PATH_DATASET.joinpath('train')
PATH_DATASET_VAL = PATH_DATASET.joinpath('val')


class PrepareDataset():
    JP_DVD = dvd_full
    JP_BD = bd_full

    def prepare(self) -> Datasets:
        print("Preparing the filtered LR and HR clips...")
        for prop, val in PROPS_DVD:
            self.JP_DVD = self.JP_DVD.std.SetFrameProp(prop, intval=val)

        for prop, val in PROPS_BD:
            self.JP_BD = self.JP_BD.std.SetFrameProp(prop, intval=val)

        prep_lr = self.prepare_lr(self.JP_DVD)
        prep_hr = self.prepare_hr(self.JP_BD, self.JP_DVD)

        # We train this on HALF (yes, you read that right) the total frames to get a beefy dataset
        if (length := self.JP_DVD.num_frames) == self.JP_DVD.num_frames:
            frames = sorted(random.sample(population=range(length), k=round(length/2)))
        else:
            raise IndexError("LR and HR aren't the same length!")

        print("Splicing LR and HR clips...")
        lr_ = core.std.Splice([prep_lr[f] for f in frames])
        hr_ = core.std.Splice([prep_hr[f] for f in frames])

        return Datasets(hr=ClipForDatasets(hr_, 'HR'),
                        lr=ClipForDatasets(lr_, 'LR'))

    def prepare_hr(self, clip: vs.VideoNode, dvd_clip: vs.VideoNode) -> vs.VideoNode:
        """
        Match with the DVD @640x480:
            bd.resize.Bicubic(720, 486, src_left=-0.75).std.Crop(top=3, bottom=3)
        """
        import havsfunc as haf
        import lvsfunc as lvf
        import muvsfunc as muf
        import rekt
        import vardefunc as vdf
        from awsmfunc import bbmod
        from vsutil import depth, join, plane
        from xvs import WarpFixChromaBlend

        rkt = rekt.rektlvls(
            clip,
            [0, 1079], [17, 16],
            [0, 1, 2, 3] + [1917, 1918, 1919], [16, 4, -2, 2] + [-2, 5, 14]
        )
        ef = bbmod(rkt, left=4, right=3, y=False)

        clip = depth(ef, 32).std.AssumeFPS(fpsnum=24, fpsden=1)

        bd_descale = lvf.kernels.Bicubic().descale(plane(clip, 0), 1280, 720)
        bd_doubled = vdf.scale.nnedi3_upscale(bd_descale)
        bd_down = muf.SSIM_downsample(bd_doubled, dvd_clip.width*2, 486*2)

        # Need to do some fuckery to make sure the chroma matches up perfectly
        bd_cshift = clip.resize.Bicubic(chromaloc_in=1, chromaloc=0, format=vs.YUV420P16)
        bd_cwarp = bd_cshift.warp.AWarpSharp2(thresh=88, blur=3, type=1, depth=6, planes=[1, 2])
        bd_chroma = bd_cwarp.resize.Bicubic(format=vs.YUV444P16, width=bd_down.width, height=bd_down.height)
        bd_i444 = core.std.ShufflePlanes([depth(bd_down, 16), bd_chroma])
        bd_shift = bd_i444.resize.Bicubic(src_left=-0.75).std.Crop(top=6, bottom=6)

        return bd_shift.resize.Bicubic(format=vs.RGB24, dither_type='error_diffusion') \
            .std.ShufflePlanes([1, 2, 0], vs.RGB)

    def prepare_lr(self, clip: vs.VideoNode) -> vs.VideoNode:
        from vardefunc.scale import to_444
        from vsutil import depth

        clip = depth(clip, 32).std.AssumeFPS(fpsnum=24, fpsden=1)
        dvd_i444 = to_444(clip, clip.width, clip.height, join_planes=True)

        return dvd_i444.resize.Bicubic(format=vs.RGB24, dither_type='error_diffusion') \
            .std.ShufflePlanes([1, 2, 0], vs.RGB)


class ExportDataset:  # noqa: PLC0115
    def write_image_async(self, dataset: Datasets) -> None:  # noqa: PLC0116
        # This method is slower :(
        print('Extract LR...')
        self._output_images(dataset.lr)
        print('Extract HR...')
        self._output_images(dataset.hr)

    @staticmethod
    def _output_images(clip_dts: ClipForDatasets) -> None:
        if not (path := PATH_DATASET_TRAIN.joinpath(clip_dts.res_type)).exists():
            path.mkdir(parents=True)

        # Pretty progress bar
        progress = Progress(TextColumn("{task.description}"), BarColumn(),
                            TextColumn("{task.completed}/{task.total}"),
                            TextColumn("{task.percentage:>3.02f}%"),
                            FPSColumn(), TimeRemainingColumn())

        with progress:
            task = progress.add_task('Extracting frames...', total=clip_dts.clip.num_frames)

            def _cb(n: int, f: vs.VideoFrame) -> None:  # noqa: PLC0103
                progress.update(task, advance=1)

            clip = clip_dts.clip.imwri.Write(
                'PNG', filename=str(path.joinpath('%06d.png'))
            )

            clip_async_render(clip, progress=None, callback=_cb)

    def write_video(self, dataset: Datasets) -> None:  # noqa: PLC0116
        print('Encoding and extracting LR...')
        self._encode_and_extract(dataset.lr)
        print('Encoding and extracting HR...')
        self._encode_and_extract(dataset.hr)

    @staticmethod
    def _encode_and_extract(clip_dts: ClipForDatasets) -> None:
        if not (path := PATH_DATASET_TRAIN.joinpath(clip_dts.res_type)).exists():
            path.mkdir(parents=True)

        params = [
            'ffmpeg', '-hide_banner', '-f', 'rawvideo',
            '-video_size', f'{clip_dts.clip.width}x{clip_dts.clip.height}',
            '-pixel_format', 'gbrp', '-framerate', str(clip_dts.clip.fps),
            '-i', 'pipe:',
            path.joinpath('%06d.png')
        ]

        print('Encoding...\n')
        with subprocess.Popen(params, stdin=subprocess.PIPE) as process:  # type: ignore
            clip_dts.clip.output(cast(BinaryIO, process.stdin))

    @staticmethod
    def select_val_images(dataset: Datasets, number: int) -> None:  # noqa: PLC0116
        if not (path_val_hr := PATH_DATASET_VAL.joinpath(dataset.hr.res_type)).exists():
            path_val_hr.mkdir(parents=True)
        if not (path_val_lr := PATH_DATASET_VAL.joinpath(dataset.lr.res_type)).exists():
            path_val_lr.mkdir(parents=True)

        if not (path_train_hr := PATH_DATASET_TRAIN.joinpath(dataset.hr.res_type)).exists():
            raise FileNotFoundError(f'{path_train_hr} not found')
        if not (path_train_lr := PATH_DATASET_TRAIN.joinpath(dataset.lr.res_type)).exists():
            raise FileNotFoundError(f'{path_train_lr} not found')

        images_path = sorted(path_train_hr.glob('*.png'))
        image_idx = random.sample(population=range(len(images_path)), k=number)

        for i in image_idx:
            name = images_path[i].name
            os.system(f'copy "{path_train_hr.joinpath(name)}" "{path_val_hr.joinpath(name)}"')
            os.system(f'copy "{path_train_lr.joinpath(name)}" "{path_val_lr.joinpath(name)}"')


if __name__ == '__main__':
    dts = PrepareDataset().prepare()

    print("Exporting dataset...")
    # ExportDataset().write_image_async(dts)  # Too slow
    ExportDataset().write_video(dts)
    ExportDataset.select_val_images(dts, 20)
else:
    # PrepareDataset().JP_DVD.set_output(0)
    # PrepareDataset().JP_BD.set_output(1)

    # dts = PrepareDataset().prepare()
    hr = PrepareDataset().prepare_hr(bd_full, dvd_full).text.FrameProps()
    lr = PrepareDataset().prepare_lr(dvd_full).resize.Bicubic(hr.width, hr.height)
    lr.text.FrameProps().set_output(0)
    hr.set_output(1)
    bd_full.set_output(2)
