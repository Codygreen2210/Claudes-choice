#!/bin/bash
# Send the glass floor Short to the Blender farm with its assets.   bash farm.sh TAG F0 F1 CH SAMPLES SCALE [stride|redo JSON]
set -e
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
A=/root/vt/assets; G=studio/samples/blender/glass; tag=$1; f0=$2; f1=$3; ch=$4; sp=$5; sc=$6; kind=$7; js=$8
id=$(date +%Y%m%d-%H%M%S)-glass-$tag
env=$(mktemp); printf 'GLB=%s/glass.py\nF0=%s\nF1=%s\nCH=%s\nSAMPLES=%s\nSCALE=%s\n' $G $f0 $f1 $ch $sp $sc > $env
idx=$(mktemp -u); export GIT_INDEX_FILE=$idx
git read-tree HEAD
add() { git update-index --add --cacheinfo 100644,$(git hash-object -w "$1"),"$2"; }
add $env render/blend.env
add /root/vt/n45/boat/man.blend $G/man.blend
add $A/kloofendal_48d_partly_cloudy_puresky/kloofendal_48d_partly_cloudy_puresky_2k.hdr $G/assets/kloofendal_48d_partly_cloudy_puresky/kloofendal_48d_partly_cloudy_puresky_2k.hdr
for f in $(cd $A/covered_car && find . -type f | sed 's|^\./||'); do add $A/covered_car/$f $G/assets/covered_car/$f; done
add /root/vt/mh/packs/keep/r2/skins/jartur69_middleage_slavic_male_with_genitals_and_beard/Jartur_mid_old_Slavic_Male_with_Genitals_and_Beard_lsdif_lighter_2k.jpg $G/assets/jartur/Jartur_mid_old_Slavic_Male_with_Genitals_and_Beard_lsdif_lighter_2k.jpg
[ -n "$kind" ] && add $js $G/$kind.json
tree=$(git write-tree); unset GIT_INDEX_FILE; rm -f $idx $env
c=$(git commit-tree $tree -p HEAD -m "blender script job $id")
git push -q https://github.com/Codygreen2210/Claudes-choice.git $c:refs/heads/render/blend-$id 2>&1 | grep -v '^remote' || true
echo $id
