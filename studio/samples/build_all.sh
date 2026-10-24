#!/usr/bin/env bash
# One command per style sample, start to finished mp4.   bash build_all.sh [1|2|3|all]
set -e
cd "$(dirname "$0")"
export PATH=/opt/node22/bin:$PATH
t0(){ date +%s.%N; }; el(){ echo "$(echo "$(date +%s.%N) - $1" | bc)"; }
lvl=${1:-all}
[ -f web/char/guy.bin ] || python3 char/character.py web/char > /dev/null   # the sculpted, skinned guy (~30 s, once)
if [[ $lvl == 1 || $lvl == all ]]; then s=$(t0)
  (cd l1 && python3 l1.py ../l1_pic.mp4 >/dev/null)
  python3 audio.py 1 l1_mix.wav >/dev/null
  ffmpeg -y -loglevel error -i l1_pic.mp4 -i l1_mix.wav -c:v copy -c:a aac -b:a 192k -shortest s1_handdrawn.mp4
  echo "LEVEL 1 total $(el $s) s"; fi
if [[ $lvl == 2 || $lvl == all ]]; then s=$(t0)
  (cd web && node render2.mjs "scene.html?level=2" 150 2>/dev/null) | python3 finish.py l2_pic.mp4 2>/dev/null
  (cd web && node track.mjs "scene.html?level=2" ../track2.json 151 >/dev/null)
  python3 audio.py 2 l2_mix.wav >/dev/null
  ffmpeg -y -loglevel error -i l2_pic.mp4 -i l2_mix.wav -c:v copy -c:a aac -b:a 192k -shortest s2_3d.mp4
  echo "LEVEL 2 total $(el $s) s"; fi
if [[ $lvl == 3 || $lvl == all ]]; then s=$(t0)
  python3 lavasim.py action_times.json >/dev/null
  (cd web && node render2.mjs "scene.html?level=3" 150 2>/dev/null) | python3 finish.py l3_pic.mp4 --grade 2>/dev/null
  (cd web && node track.mjs "scene.html?level=3" ../track3.json 151 >/dev/null)
  python3 audio.py 3 l3_mix.wav >/dev/null
  ffmpeg -y -loglevel error -i l3_pic.mp4 -i l3_mix.wav -c:v copy -c:a aac -b:a 192k -shortest s3_cinematic.mp4
  echo "LEVEL 3 total $(el $s) s"; fi
