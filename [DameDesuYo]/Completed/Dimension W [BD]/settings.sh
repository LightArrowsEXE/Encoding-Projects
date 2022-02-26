#!/bin/bash

time for f in *.vpy; do
    printf "\nEncoding audio for \"$(basename "$f" .vpy)\" (AAC and FLAC)\n";
    python "ac_$(basename "$f" .vpy).py"; # Re-encoding PCM again because qaac throws a fit otherwise
    ffmpeg -i "$(basename $f .vpy)_cut.mka" -loglevel panic -stats "$(basename $f .vpy)_cut.wav";
    eac3to "$(basename $f .vpy)_cut.wav" -log=NUL "$(basename $f .vpy)_cut.flac";
    qaac "$(basename $f .vpy)_cut.wav" -V 127 --no-delay -o "$(basename $f .vpy)_cut.m4a";

    printf "\nGenerating keyframes and timecode file if necessary\n";
    vspipe "$f" --info .;

    printf "\n\nEncoding \"$(basename "$f" .vpy) (720p)\":\n";
    time vspipe "$f" --y4m - | x264-djatom --frames "$(vspipe --info "$f" - | grep -oP "Frames:\s*\K\d+")" --demuxer y4m -o "$(basename "$f" .vpy)_720p.264" - \
    --fps 24000/1001 --range tv --colormatrix bt709 --colorprim bt709 --transfer bt709 \
    --preset veryslow --crf 14 --keyint 360 --min-keyint 23 --ref 16 --bframes 16 \
    --deblock -2:-2 --aq-mode 3 --aq-strength 0.95 --qcomp 0.65 --no-mbtree --me tesa --merange 32 \
    --direct spatial --no-dct-decimate --no-fast-pskip --psy-rd 0.85:0.0 --fade-compensate 0.4 \
    --output-depth 10 --output-csp i444 --qpfile "keyframes/$(basename "$f" .vpy)_keyframes.txt";

    printf "\nPreparing a premux for \"$(basename "$f" .vpy) (720p)\"\n";
    time mkvmerge -o "Premux/$(basename $f .vpy) - 720p (Premux).mkv" -v "$(basename $f .vpy)_720p.264" "$(basename $f .vpy)_cut.m4a";

    printf "\nEncoding \"$(basename "$f" .vpy) (1080p)\":\n";
    time vspipe "$f" -a "enc_1080=True" --y4m - | x264-djatom --frames "$(vspipe --info "$f" - | grep -oP "Frames:\s*\K\d+")" --demuxer y4m -o "$(basename "$f" .vpy)_1080p.264" - \
    --fps 24000/1001 --range tv --colormatrix bt709 --colorprim bt709 --transfer bt709 \
    --preset veryslow --crf 15 --keyint 360 --min-keyint 23 --ref 16 --bframes 16 \
    --deblock -2:-2 --aq-mode 3 --aq-strength 0.95 --qcomp 0.65 --no-mbtree --me tesa --merange 32 \
    --direct spatial --no-dct-decimate --no-fast-pskip --psy-rd 0.85:0.0 --fade-compensate 0.4 \
    --output-depth 10 --qpfile "keyframes/$(basename "$f" .vpy)_keyframes.txt";

    printf "\nPreparing a premux for \"$(basename "$f" .vpy) (1080p)\"\n";
    time mkvmerge -o "Premux/$(basename $f .vpy) - 1080p (Premux).mkv" -v "$(basename $f .vpy)_1080p.264" "$(basename $f .vpy)_cut.flac";
done
