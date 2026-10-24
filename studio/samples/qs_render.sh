#!/bin/bash
# Chunked final render for the quicksand Short (a fresh browser per chunk, so one hang can't stall the whole job).
#   bash qs_render.sh WORKDIR [FIRST_FRAME] [CHUNK]      -> WORKDIR/seg_*.mp4, then WORKDIR/pic.mp4 + final.mp4
set -e
cd "$(dirname "$0")"
d=$1; f0=${2:-0}; ch=${3:-180}
N=$(python3 -c "import json;print(round(json.load(open('web/qs/times.json'))['total']*30))")
for ((s=f0; s<N; s+=ch)); do e=$((s+ch)); ((e>N)) && e=$N
  out=$(printf "%s/seg_%05d.mp4" "$d" $s)
  [ -f "$out" ] && continue
  (cd web && timeout 1800 node render2.mjs quick.html $e 1080 1920 $s 2>>$d/render.log) | python3 qs_finish.py "$out.part.mp4" web/qs/times.json web/qs/lines.json --start $s 2>>$d/render.log
  n=$(ffprobe -v error -count_frames -select_streams v -show_entries stream=nb_read_frames -of csv=p=0 "$out.part.mp4")
  if [ "$n" = "$((e-s))" ]; then mv "$out.part.mp4" "$out"; echo "chunk $s-$e ok" >> $d/render.log; else echo "chunk $s-$e short ($n), retry" >> $d/render.log; rm -f "$out.part.mp4"; s=$((s-ch)); fi
done
ls $d/seg_*.mp4 | sed "s/^/file '/; s/$/'/" > $d/segs.txt
ffmpeg -y -loglevel error -f concat -safe 0 -i $d/segs.txt -c copy $d/pic.mp4
ffmpeg -y -loglevel error -i $d/pic.mp4 -i $d/mix.wav -c:v copy -c:a aac -b:a 192k -shortest $d/final.mp4
echo DONE >> $d/render.log
