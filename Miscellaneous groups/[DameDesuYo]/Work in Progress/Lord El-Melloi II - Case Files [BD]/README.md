Note: I'm doing a mixed 720p/AAC, 1080p/FLAC release upon request. Thus, the two scripts will be fairly different. If you use them, make sure you use the correct script to suit your needs. If you want to encode it in 720p, use the 720p script. Same with 1080p.
<br><br><br><br><br>
<div style="text-align:center; height:600px;"><img src="74542691_p0_master1200.jpg" /></div>

## Settings:

### 720p
```
vspipe casefilesBD_00_720.vpy --y4m - | x264 --demuxer y4m -o casefilesBD_00_720.264 - --preset veryslow --crf 14 --keyint 360 --min-keyint 23 --ref 16 --bframes 16 --aq-mode 3 --aq-strength 0.65 --qcomp 0.70 --no-dct-decimate --no-fast-pskip --psy-rd 0.72:0.0 --output-depth 10 --output-csp i444
```

### 1080p
```
vspipe casefilesBD_00_1080.vpy --y4m - | x264 --demuxer y4m -o casefilesBD_00_1080.264 - --preset veryslow --crf 14 --keyint 360 --min-keyint 23 --ref 16 --bframes 16 --aq-mode 3 --aq-strength 0.65 --qcomp 0.70 --no-dct-decimate --no-fast-pskip --psy-rd 0.72:0.0 --output-depth 10
```

The settings file will be omitted in this directory.