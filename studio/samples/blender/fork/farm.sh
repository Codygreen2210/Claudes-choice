#!/bin/bash
# Send the fork-in-the-microwave Short to the Blender farm with its assets.   bash farm.sh TAG F0 F1 CH SAMPLES SCALE [stride|redo JSON]
set -e
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
G=studio/samples/blender/fork; tag=$1; f0=$2; f1=$3; ch=$4; sp=$5; sc=$6; kind=$7; js=$8
id=$(date +%Y%m%d-%H%M%S)-fork-$tag
env=$(mktemp); printf 'GLB=%s/fork.py\nF0=%s\nF1=%s\nCH=%s\nSAMPLES=%s\nSCALE=%s\n' $G $f0 $f1 $ch $sp $sc > $env
idx=$(mktemp -u); export GIT_INDEX_FILE=$idx
git read-tree HEAD
add() { git update-index --add --cacheinfo 100644,$(git hash-object -w "$1"),"$2"; }
add $env render/blend.env
# the prop-studio assets this scene loads (kitchen HDRI, marble counter, wood cabinet)
python3 -c "
import sys; sys.path.insert(0, 'studio/props'); import props_bpy as P
for a, b in P.farm_files(['ph:cayley_interior', 'acg:Marble016', 'ph:kitchen_wood'], '$G').items(): print(a, b)
" | while read a b; do add "$a" "$b"; done
[ -n "$kind" ] && add $js $G/$kind.json
tree=$(git write-tree); unset GIT_INDEX_FILE; rm -f $idx $env
c=$(git commit-tree $tree -p HEAD -m "blender script job $id")
git push -q https://github.com/Codygreen2210/Claudes-choice.git $c:refs/heads/render/blend-$id 2>&1 | grep -v '^remote' || true
echo $id
