#!/bin/bash
# Captions over the Blender render, then the sound:  bash finish.sh WORKDIR   (needs WORKDIR/shot.mp4 and mix.wav)
# qs_finish.py flips each frame (made for bottom-up WebGL reads), so the Blender frames go in pre-flipped with vflip
set -e
here=$(cd "$(dirname "$0")" && pwd); d=$1; cd $here/../..
# the grade: a soft glow off the bright bits (lights, ribbon, x-ray bones), a light vignette, a touch more color
G="format=gbrp,split[a][b];[b]curves=all='0/0 0.6/0 1/1',gblur=sigma=30[g];[a][g]blend=all_mode=screen:all_opacity=0.5,vignette=PI/5,eq=saturation=1.1:contrast=1.04"
ffmpeg -loglevel error -i $d/shot.mp4 -filter_complex "$G,scale=1080:1920,vflip" -f rawvideo -pix_fmt rgba -s 1080x1920 - | python3 qs_finish.py $d/pic.mp4 $here/times.json $here/lines.json --cfg $here/finish.json
ffmpeg -y -loglevel error -i $d/pic.mp4 -i $d/mix.wav -c:v copy -c:a aac -b:a 192k $d/final.mp4
echo "final: $d/final.mp4"
