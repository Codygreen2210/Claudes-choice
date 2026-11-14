#!/bin/bash
# bash farm.sh TAG F0 F1 CH SAMPLES SCALE [stride|redo JSONFILE]  -> pushes render/blend-<id> with man.blend (+ stride/redo json); prints id
# Run from the studio/animate checkout with sunz/ committed and pushed; man.blend comes from /root/vt/n44/sun/zack (or $MAN).
set -e
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
tag=$1; f0=$2; f1=$3; ch=$4; sp=$5; sc=$6; kind=$7; js=$8
man=${MAN:-/root/vt/n44/sun/zack/man.blend}
id=$(date +%Y%m%d-%H%M%S)-sunz-$tag
env=$(mktemp); printf 'GLB=studio/samples/blender/sunz/sunz.py\nF0=%s\nF1=%s\nCH=%s\nSAMPLES=%s\nSCALE=%s\n' $f0 $f1 $ch $sp $sc > $env
idx=$(mktemp -u); export GIT_INDEX_FILE=$idx
git read-tree HEAD
git update-index --add --cacheinfo 100644,$(git hash-object -w $env),render/blend.env
git update-index --add --cacheinfo 100644,$(git hash-object -w $man),studio/samples/blender/sunz/man.blend
[ -n "$kind" ] && git update-index --add --cacheinfo 100644,$(git hash-object -w $js),studio/samples/blender/sunz/$kind.json
tree=$(git write-tree); unset GIT_INDEX_FILE; rm -f $idx $env
c=$(git commit-tree $tree -p HEAD -m "blender script job $id")
git push -q origin $c:refs/heads/render/blend-$id 2>&1 | grep -v '^remote' || true
echo $id
