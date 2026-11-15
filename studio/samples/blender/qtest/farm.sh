#!/bin/bash
# Send the quality test to the Blender farm with its Poly Haven assets.   bash farm.sh TAG F0 F1 CH SAMPLES SCALE
set -e
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
A=/root/vt/assets; tag=$1; f0=$2; f1=$3; ch=$4; sp=$5; sc=$6
id=$(date +%Y%m%d-%H%M%S)-qtest-$tag
env=$(mktemp); printf 'GLB=studio/samples/blender/qtest/qtest.py\nF0=%s\nF1=%s\nCH=%s\nSAMPLES=%s\nSCALE=%s\n' $f0 $f1 $ch $sp $sc > $env
idx=$(mktemp -u); export GIT_INDEX_FILE=$idx
git read-tree HEAD
git update-index --add --cacheinfo 100644,$(git hash-object -w $env),render/blend.env
for f in brown_photostudio_02/brown_photostudio_02_2k.hdr oak_veneer_01/oak_veneer_01_diff_2k.jpg oak_veneer_01/oak_veneer_01_rough_2k.jpg oak_veneer_01/oak_veneer_01_nor_gl_2k.jpg; do
  git update-index --add --cacheinfo 100644,$(git hash-object -w $A/$f),studio/samples/blender/qtest/assets/$f
done
tree=$(git write-tree); unset GIT_INDEX_FILE; rm -f $idx $env
c=$(git commit-tree $tree -p HEAD -m "blender script job $id")
git push -q https://github.com/Codygreen2210/Claudes-choice.git $c:refs/heads/render/blend-$id 2>&1 | grep -v '^remote' || true
echo $id
