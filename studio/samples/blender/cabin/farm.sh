#!/bin/bash
# bash farm.sh TAG F0 F1 CH SAMPLES SCALE [stride|redo JSONFILE]  -> pushes render/blend-<id> with man.blend (+ stride/redo json); prints id
set -e
cd /home/claude/claudes-choice
tag=$1; f0=$2; f1=$3; ch=$4; sp=$5; sc=$6; kind=$7; js=$8
id=$(date +%Y%m%d-%H%M%S)-cabin-$tag
env=$(mktemp); printf 'GLB=studio/samples/blender/cabin/cabin.py\nF0=%s\nF1=%s\nCH=%s\nSAMPLES=%s\nSCALE=%s\n' $f0 $f1 $ch $sp $sc > $env
idx=$(mktemp -u); export GIT_INDEX_FILE=$idx
git read-tree HEAD
git update-index --add --cacheinfo 100644,$(git hash-object -w $env),render/blend.env
for f in man.blend lungs.blend; do git update-index --add --cacheinfo 100644,$(git hash-object -w /root/vt/n42/cabin/$f),studio/samples/blender/cabin/$f; done
[ -n "$kind" ] && git update-index --add --cacheinfo 100644,$(git hash-object -w $js),studio/samples/blender/cabin/$kind.json
tree=$(git write-tree); unset GIT_INDEX_FILE; rm -f $idx $env
c=$(git commit-tree $tree -p HEAD -m "blender script job $id")
git push -q origin $c:refs/heads/render/blend-$id 2>&1 | grep -v '^remote' || true
echo $id
