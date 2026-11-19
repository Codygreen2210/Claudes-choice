#!/bin/bash
# Send the Emu War cut-out style animation to the Blender farm with its art and assets.   bash farm.sh TAG F0 F1 CH SAMPLES SCALE
set -e
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
G=studio/samples/blender/emu3d; tag=$1; f0=$2; f1=$3; ch=$4; sp=$5; sc=$6
id=$(date +%Y%m%d-%H%M%S)-emu-$tag
env=$(mktemp); printf 'GLB=%s/%s\nF0=%s\nF1=%s\nCH=%s\nSAMPLES=%s\nSCALE=%s\n' $G ${SCRIPT:-anim.py} $f0 $f1 $ch $sp $sc > $env
idx=$(mktemp -u); export GIT_INDEX_FILE=$idx
git read-tree HEAD
add() { git update-index --add --cacheinfo 100644,$(git hash-object -w "$1"),"$2"; }
add $env render/blend.env
for f in $G/art/*.png $G/art/contours.json; do add $f $f; done          # pngs are git-ignored here, so they go in by hand
python3 -c "
import sys; sys.path.insert(0, 'studio/props'); import props_bpy as P
for a, b in P.farm_files(['acg:Cardboard004', 'ph:velour_velvet', 'ph:old_wooden_floor_01', 'ph:theater_01'], '$G').items(): print(a, b)
" | while read a b; do add "$a" "$b"; done
tree=$(git write-tree); unset GIT_INDEX_FILE; rm -f $idx $env
c=$(git commit-tree $tree -p HEAD -m "blender script job $id")
git push -q https://github.com/Codygreen2210/Claudes-choice.git $c:refs/heads/render/blend-$id 2>&1 | grep -v '^remote' || true
echo $id
