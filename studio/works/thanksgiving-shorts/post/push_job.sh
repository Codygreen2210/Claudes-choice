#!/bin/bash
# push_job.sh SCRIPT F0 F1 CH SAMPLES SCALE  -> pushes render/thanks-<id>, prints id
set -e
cd /home/claude/claudes-choice
git fetch -q --depth 1 origin main
id=$(date +%Y%m%d-%H%M%S)-${1%.py}
env=$(mktemp); printf 'SCRIPT=%s\nF0=%s\nF1=%s\nCH=%s\nSAMPLES=%s\nSCALE=%s\n' $1 $2 $3 $4 $5 $6 > $env
idx=$(mktemp -u); export GIT_INDEX_FILE=$idx
git read-tree FETCH_HEAD
add() { git update-index --add --cacheinfo 100644,$(git hash-object -w $1),$2; }
add /home/claude/work/farm/thanks-farm.yml .github/workflows/thanks-farm.yml
add $env render/thanks.env
for f in tg_lib.py turkey3d.py coma3d.py turkey_raw.npz turkey_roast.npz turkey_times.json coma_times.json; do
  [ -f /home/claude/work/b3d/$f ] && add /home/claude/work/b3d/$f studio/samples/blender/thanks/$f
done
tree=$(git write-tree); unset GIT_INDEX_FILE; rm -f $idx $env
c=$(git commit-tree $tree -p FETCH_HEAD -m "thanks job $id")
git push -q origin $c:refs/heads/render/thanks-$id
echo $id
