#!/usr/bin/env bash
# Build one Short: sound -> ears check -> picture -> final.mp4
#   GEN=12 bash studio/toon/shorts/build.sh <name>
# Work dir: $VT/n$GEN/<name>/ must already hold lines.json, times.json, narration.wav (from narrate_short.py).
n=$1; VT=${VT:-$HOME/vt}; d=$VT/n${GEN:-1}/$n
HERE=$(cd "$(dirname "$0")" && pwd); KIT=${STUDIO_ROOT:-$VT/kit}
cd "$HERE" && STUDIO_ROOT=$KIT python3 body_sound.py "$n" "$d/times.json" "$d/narration.wav" "$d/mix.wav" || exit 2
cd "$HERE/../../senses" && STUDIO_ROOT=$KIT python3 listen.py "$d/mix.wav" > "$d/ears.txt" 2>&1
cd "$HERE" && python3 "$n.py" "$d/times.json" "$d/lines.json" "$d/pic.mp4" || exit 1
# keep every picture frame (-shortest with a copied video stream was dropping the last few, which broke the loop seam):
# pad the sound with silence and cut at the picture's own length
pdur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$d/pic.mp4")
ffmpeg -y -loglevel error -i "$d/pic.mp4" -i "$d/mix.wav" -c:v copy -af apad -c:a aac -b:a 192k -t "$pdur" "$d/final.mp4"
echo "done $n -> $d/final.mp4"
