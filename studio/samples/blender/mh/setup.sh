#!/bin/bash
# MakeHuman character kit (all CC0 for what we make): MPFB2 (Blender extension) + MakeHuman system assets.
# Only GitHub is reachable from the studio workspace; the assets repo stores images in Git LFS, which the git proxy
# doesn't serve, so images come from media.githubusercontent.com instead.
#   bash setup.sh            -> installs MPFB into bpy, copies assets to its user data dir, tans the skin, makes the shirt teal (logo painted out)
set -e
M=/home/claude/mh; mkdir -p $M; cd $M
[ -d mpfb2 ] || GIT_LFS_SKIP_SMUDGE=1 git clone -q --filter=blob:none --no-checkout --depth 1 https://github.com/makehumancommunity/mpfb2
[ -d makehuman ] || GIT_LFS_SKIP_SMUDGE=1 git clone -q --filter=blob:none --no-checkout --depth 1 https://github.com/makehumancommunity/makehuman
[ -d mpa ] || GIT_LFS_SKIP_SMUDGE=1 git clone -q --filter=blob:none --no-checkout --depth 1 https://github.com/dmaugis/makehuman-py3-assets mpa
(cd mpfb2 && git checkout -q HEAD -- src) ; (cd makehuman && git checkout -q HEAD -- makehuman/data/eyes)
sel="base/clothes/male_casualsuit06 base/clothes/shoes05 base/hair/short02 base/skins/young_caucasian_male base/eyes base/eyebrows/eyebrow001 base/eyelashes/eyelashes01 base/teeth base/tongue"
cd mpa && git checkout -q HEAD -- $(git ls-tree -r --name-only HEAD $sel | grep -vE "\.(png|jpg|tif|bmp)$")
for p in $(git ls-tree -r --name-only HEAD $sel | grep -E "\.png$") base/skins/textures/young_lightskinned_male_diffuse.png base/skins/textures/young_lightskinned_male_diffuse2.png; do
  mkdir -p $(dirname $p); curl -s -L -m 120 -o "$p" "https://media.githubusercontent.com/media/dmaugis/makehuman-py3-assets/master/$p"; done
cd $M && rm -f mpfb.zip && (cd mpfb2/src && zip -qr ../../mpfb.zip mpfb)
python3 -c "import bpy; bpy.ops.extensions.package_install_files(filepath='$M/mpfb.zip', repo='user_default', enable_on_install=True); bpy.ops.wm.save_userpref()"
D=/root/.config/blender/5.2/extensions/.user/user_default/mpfb/data; mkdir -p $D
cp -r mpa/base/{skins,clothes,hair,eyes,eyebrows,eyelashes,teeth,tongue} $D/; cp -r makehuman/makehuman/data/eyes/{high-poly,low-poly} $D/eyes/; cp makehuman/makehuman/data/eyes/materials/* $D/eyes/materials/
python3 "$(dirname "$0")/prep_textures.py" $D
