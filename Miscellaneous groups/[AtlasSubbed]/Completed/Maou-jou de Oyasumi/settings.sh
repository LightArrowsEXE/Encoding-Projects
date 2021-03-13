#!/bin/bash

time for f in *.vpy; do
    printf "\nEncoding \"$(basename "$f" .vpy)\"\n";
    time vspipe "$f" --y4m - | \
    x264 --demuxer y4m -o "$(basename "$f" .vpy).264" - \
    --fps 24000/1001 --colormatrix bt709 --colorprim bt709 --transfer bt709 \
    --preset veryslow --crf 16 --keyint 360 --min-keyint 23 --ref 16 --bframes 16 \
    --deblock -2:-2 --aq-mode 3 --aq-strength 0.85 --qcomp 0.70 --me umh \
    --direct spatial --no-dct-decimate --no-fast-pskip \
    --psy-rd 0.72:0.0 --output-depth 10;
done