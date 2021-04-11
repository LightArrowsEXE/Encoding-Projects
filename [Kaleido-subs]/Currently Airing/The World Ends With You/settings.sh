#!/bin/bash

for f in *.vpy; do
    printf "\nGenerating keyframes and timecode file if necessary\n";
    vspipe "$f" --info .;

    printf "\nEncoding \"$(basename "$f" .vpy)\"\n";
    time vspipe "$f" --y4m - | \
    x265 --frames "$(vspipe --info "$f" - | grep -oP "Frames:\s*\K\d+")" \
    --y4m -o "$(basename $f .vpy).265" - \
    --fps 24000/1001 --sar 1 --videoformat ntsc --range limited \
    --colormatrix bt709 --colorprim bt709 --transfer bt709 \
    --preset veryslow --crf 15 --deblock=-2:-2 --keyint 240 --min-keyint 23  --ref 6 --bframes 16  \
    --aq-mode 3 --aq-strength 0.85 --qcomp 0.70 --cbqpoffs -2 --crqpoffs -2 --rc-lookahead 60 \
    --rd 3 --rdoq-level 2 --psy-rd 1.75 --psy-rdoq 2.0 --cutree \
    --no-open-gop --b-intra --weightb --tskip --no-strong-intra-smoothing --no-sao --no-sao-non-deblock \
    --output-depth 10 --qpfile "keyframes/$(basename "$f" .vpy)_keyframes.txt";

    printf "\nEncoding audio for \"$(basename "$f" .vpy)\"\n";
    python "ac_$(basename "$f" .vpy).py";

    printf "\nPreparing a premux for \"$(basename "$f" .vpy)\"\n";
    time mkvmerge -o "Premux/$(basename $f .vpy) (Premux).mkv" -v "$(basename $f .vpy).265" "$(basename $f .vpy)_cut.mka";
done
