#!/bin/bash

TIMEFORMAT=%0lR

time for f in *.vpy; do
    printf "\nGenerating keyframes and timecode file if necessary\n";
    vspipe "$f" --info -;

    printf "\nEncoding \"$(basename "$f" .vpy)\"\n";
    time vspipe "$f" --y4m - | \
    x264 --frames "$(vspipe --info "$f" - | grep -oP "Frames:\s*\K\d+")" --demuxer y4m -o "$(basename "$f" .vpy).264" - \
    --fps 24000/1001 --range tv --colormatrix bt709 --colorprim bt709 --transfer bt709 \
    --preset veryslow --crf 16 --keyint 360 --min-keyint 23 --ref 16 --bframes 16 \
    --no-mbtree --deblock -2:-2 --aq-mode 3 --aq-strength 1.0 --qcomp 0.65 --me tesa --merange 32 \
    --direct spatial --no-dct-decimate --no-fast-pskip --psy-rd 1.0:0.0 \
    --output-depth 10 --qpfile "keyframes/$(basename "$f" .vpy)_keyframes.txt";

    printf "\nEncoding audio for \"$(basename "$f" .vpy)\"\n";
    python "ac_$(basename "$f" .vpy).py"; # Re-encoding PCM again because qaac throws a fit otherwise
    ffmpeg -i "$(basename $f .vpy)_cut.mka" -loglevel panic -stats "$(basename $f .vpy)_cut.wav";
    qaac "$(basename $f .vpy)_cut.wav" -V 127 --no-delay -o "$(basename $f .vpy)_cut.m4a";

    printf "\nPreparing a premux for \"$(basename "$f" .vpy)\"\n";
    time mkvmerge -o "Premux/$(basename $f .vpy) (Premux).mkv" -v "$(basename $f .vpy).264" "$(basename $f .vpy)_cut.m4a";
done
