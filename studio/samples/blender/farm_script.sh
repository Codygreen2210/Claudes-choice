#!/bin/bash
# Render a scene that builds itself in Blender (a bpy script: SCRIPT OUT F0 F1 --samples N --scale S) on the Blender farm.
# The farm's shot.py runs any GLB= path ending in .py as such a script, so the workflow itself needs no change.
#   bash farm_script.sh studio/samples/blender/clock/clock.py WORKDIR F0 F1 [CH=49] [SAMPLES=64] [SCALE=1.0]   -> WORKDIR/shot.mp4
set -e
cd "$(dirname "$0")"
script=$1; d=$2; f0=$3; f1=$4; ch=${5:-49}; sp=${6:-64}; sc=${7:-1.0}
id=$(date +%Y%m%d-%H%M%S)-$(basename ${script%.py}); root=$(git rev-parse --show-toplevel)
env=$(mktemp); printf 'GLB=%s\nF0=%s\nF1=%s\nCH=%s\nSAMPLES=%s\nSCALE=%s\n' $script $f0 $f1 $ch $sp $sc > $env
idx=$(mktemp -u); export GIT_INDEX_FILE=$idx
git read-tree HEAD
git update-index --add --cacheinfo 100644,$(git hash-object -w $env),render/blend.env
tree=$(git write-tree); unset GIT_INDEX_FILE; rm -f $idx $env
c=$(git commit-tree $tree -p HEAD -m "blender script job $id")
git push -q origin $c:refs/heads/render/blend-$id
echo "pushed render/blend-$id ($c)" >&2
t0=$(date +%s)
until git ls-remote --exit-code origin refs/heads/render/out-$id > /dev/null 2>&1; do
  (( $(date +%s) - t0 > 21600 )) && { echo "no result after 6 h" >&2; exit 1; }
  sleep 60
done
echo "result after $(( $(date +%s) - t0 )) s" >&2
mkdir -p $d/farm && git fetch -q --depth 1 origin refs/heads/render/out-$id && git -C "$root" archive FETCH_HEAD | tar -x -C $d/farm
grep -h "^chunk" $d/farm/log_*.txt | sort -n -k2 >&2 || true
want=$(( (f1 - f0 + ch - 1) / ch )); have=$(ls $d/farm/clip_*.mp4 2>/dev/null | wc -l)
[ "$have" = "$want" ] || { echo "only $have of $want clips came back; see $d/farm/log_*.txt" >&2; exit 1; }
ls $d/farm/clip_*.mp4 | sed "s/^/file '/; s/$/'/" > $d/clips.txt
ffmpeg -y -loglevel error -f concat -safe 0 -i $d/clips.txt -c copy $d/shot.mp4
echo "script $id DONE in $(( $(date +%s) - t0 )) s" >&2
