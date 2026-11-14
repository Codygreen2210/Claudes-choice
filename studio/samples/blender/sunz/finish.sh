#!/bin/bash
# qs_finish.py flips each frame (it was made for bottom-up WebGL reads), so the Blender frames go in pre-flipped with vflip
# Captions, hook, labels and readouts over the Blender render, then the sound:  bash finish.sh WORKDIR   (needs WORKDIR/shot.mp4 and mix.wav)
set -e
here=$(cd "$(dirname "$0")" && pwd); d=$1; cd $here/../..
ffmpeg -loglevel error -i $d/shot.mp4 -vf vflip,scale=1080:1920 -f rawvideo -pix_fmt rgba -s 1080x1920 - | python3 qs_finish.py $d/pic.mp4 $here/times.json $here/cap_lines.json --cfg $here/finish.json
ffmpeg -y -loglevel error -i $d/pic.mp4 -i $d/mix.wav -c:v copy -c:a aac -b:a 192k $d/final.mp4
echo "final: $d/final.mp4"
