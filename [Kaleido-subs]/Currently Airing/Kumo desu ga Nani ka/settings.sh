#!/bin/bash

time for f in *.vpy; do
    printf "\nGenerating keyframes and timecode file if necessary\n";
    vspipe "$f" --info -;

    printf "\nEncoding \"$(basename "$f" .vpy)\"\n";
    time vspipe "$f" --y4m - | x264 --frames "$(vspipe --info "$f" - | grep -oP "Frames:\s*\K\d+")" --demuxer y4m -o "$(basename "$f" .vpy).264" - \
    --fps 24000/1001 --range tv --colormatrix bt709 --colorprim bt709 --transfer bt709 \
    --preset veryslow --crf 16.5 --keyint 360 --min-keyint 23 --ref 16 --bframes 16 \
    --deblock -2:-2 --aq-mode 3 --aq-strength 0.95 --qcomp 0.70 --me tesa --merange 32 \
    --direct spatial --no-dct-decimate --no-fast-pskip --psy-rd 0.85:0.0 \
    --output-depth 10 --qpfile "keyframes/$(basename "$f" .vpy)_keyframes.txt";
done
