#!/bin/bash
# Send the frozen-turkey fryer Short to the Blender farm with its assets.   bash farm.sh TAG F0 F1 CH SAMPLES SCALE [stride|redo JSON]
# Ships the man (man.blend), his shoes (pilot.blend) and every prop-studio asset the scene loads.
set -e
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
G=studio/samples/blender/fryer3d; tag=$1; f0=$2; f1=$3; ch=$4; sp=$5; sc=$6; kind=$7; js=$8
man=${MAN:-/root/vt/n45/boat/man.blend}; pilot=${PILOT:-/root/vt/n38/g9/pilot.blend}
id=$(date +%Y%m%d-%H%M%S)-fryer3d-$tag
env=$(mktemp); printf 'GLB=%s/fryer3d.py\nF0=%s\nF1=%s\nCH=%s\nSAMPLES=%s\nSCALE=%s\n' $G $f0 $f1 $ch $sp $sc > $env
idx=$(mktemp -u); export GIT_INDEX_FILE=$idx
git read-tree HEAD
add() { git update-index --add --cacheinfo 100644,$(git hash-object -w "$1"),"$2"; }
add $env render/blend.env
add $man $G/man.blend
add $pilot $G/pilot.blend
python3 -c "
import sys; sys.path.insert(0, 'studio/props'); import props_bpy as P
ids = 'qwantani_dusk_2 leafy_grass weathered_plank_siding wood_floor_deck grey_roof_01 wooden_picnic_table metal_trash_can potted_plant_02 garden_hose_wall_mounted_01 garden_gloves_01 Lantern_01 grass_medium_01 propane_tank'.split()
for a, b in P.farm_files(['ph:' + i for i in ids], '$G').items(): print(a, b)
" | while read a b; do add "$a" "$b"; done
[ -n "$kind" ] && add $js $G/$kind.json
tree=$(git write-tree); unset GIT_INDEX_FILE; rm -f $idx $env
c=$(git commit-tree $tree -p HEAD -m "blender script job $id")
git push -q https://github.com/Codygreen2210/Claudes-choice.git $c:refs/heads/render/blend-$id 2>&1 | grep -v '^remote' || true
echo $id
