#!/bin/bash
# finish.sh NAME ID  -> /home/claude/work/final/NAME.mp4 (farm clips joined, captions + readouts burned in, mix added)
set -e
name=$1; id=$2; d=/home/claude/work/final/$name; mkdir -p $d/farm
cd /home/claude/claudes-choice
git fetch -q --depth 1 origin refs/heads/render/thanks-out-$id
git archive FETCH_HEAD | tar -x -C $d/farm
grep -h "^chunk" $d/farm/log_*.txt | sort -t' ' -k2 -n | tail -3 || true
ls $d/farm/clip_*.mp4 | sort | sed "s/^/file '/; s/$/'/" > $d/clips.txt
echo "clips: $(wc -l < $d/clips.txt)"
ffmpeg -y -loglevel error -f concat -safe 0 -i $d/clips.txt -c copy $d/render.mp4
cd /home/claude/work
python3 compose.py $name $d/render.mp4 snd/mix_$name.wav final/$name.mp4
ffprobe -v error -show_entries format=duration -of csv=p=0 final/$name.mp4
