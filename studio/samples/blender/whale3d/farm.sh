#!/bin/bash
# Send the whale Short to the Blender farm with its assets.   bash farm.sh TAG F0 F1 CH SAMPLES SCALE [stride|redo JSON]
# Ships the man (man.blend) the diver is built from; everything else is built in code.
set -e
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
G=studio/samples/blender/whale3d; tag=$1; f0=$2; f1=$3; ch=$4; sp=$5; sc=$6; kind=$7; js=$8
man=${MAN:-/root/vt/n45/boat/man.blend}
id=$(date +%Y%m%d-%H%M%S)-whale3d-$tag
env=$(mktemp); printf 'GLB=%s/whale3d.py\nF0=%s\nF1=%s\nCH=%s\nSAMPLES=%s\nSCALE=%s\n' $G $f0 $f1 $ch $sp $sc > $env
idx=$(mktemp -u); export GIT_INDEX_FILE=$idx
git read-tree HEAD
add() { git update-index --add --cacheinfo 100644,$(git hash-object -w "$1"),"$2"; }
add $env render/blend.env
add $man $G/man.blend
[ -n "$kind" ] && add $js $G/$kind.json
tree=$(git write-tree); unset GIT_INDEX_FILE; rm -f $idx $env
c=$(git commit-tree $tree -p HEAD -m "blender script job $id")
git push -q https://github.com/Codygreen2210/Claudes-choice.git $c:refs/heads/render/blend-$id 2>&1 | grep -v '^remote' || true
echo $id
