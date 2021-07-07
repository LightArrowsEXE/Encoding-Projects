#!/bin/bash

TIMEFORMAT=%0lR

time for f in *.vpy; do

    printf "\nEncoding audio for \"$(basename "$f" .vpy)\"\n";
    python "ac_$(basename "$f" .vpy).py";
    eac3to "$(basename $f .vpy)_cut.mka" -log=NUL "$(basename $f .vpy)_cut.flac";

    printf "\nGenerating additional files for \"$(basename "$f" .vpy)\" if necessary\n";
    vspipe "$f" --info .;

    printf "\nEncoding \"$(basename "$f" .vpy)\"\n";
    time vspipe "$f" --y4m - | \
    x264-djatom --frames "$(vspipe --info "$f" - | grep -oP "Frames:\s*\K\d+")" --demuxer y4m -o "$(basename "$f" .vpy).264" - \
    --fps 24000/1001 --range tv --colormatrix bt709 --colorprim bt709 --transfer bt709 \
    --preset veryslow --crf 14.5 --keyint 240 --min-keyint 23 --ref 16 --bframes 16 \
    --deblock -2:-2 --aq-mode 3 --aq-strength 0.95 --qcomp 0.70 --me tesa --merange 32 \
    --direct spatial --no-dct-decimate --no-fast-pskip --psy-rd 0.85:0.0 --fade-compensate 0.4 \
    --output-depth 10 --qpfile "keyframes/$(basename "$f" .vpy)_keyframes.txt";

    printf "\nPreparing a premux for \"$(basename "$f" .vpy)\"\n";
    time mkvmerge -o "Premux/$(basename $f .vpy) (Premux).mkv" -v "$(basename $f .vpy).264" "$(basename $f .vpy)_cut.flac";
done