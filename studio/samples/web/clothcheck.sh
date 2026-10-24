#!/bin/bash
# Cloth/skin clipping check for the 3D guy: renders him in hard poses (walk with the foot flexed, deep crouch,
# head turned with a shoulder shrug, twisted torso with a leg up) and tiles the close-ups into 3 contact sheets.
#   bash clothcheck.sh OUT_PREFIX            ->  OUT_PREFIX_s1.png (waist + feet), _s2.png (crouch/twist), _s3.png (neck)
# Look for: jeans showing through the shirt, the shoe collar through the jeans hem, neck skin through the collar.
set -e
cd "$(dirname "$0")"
P=$1
WALK='{"thighR":[-35,0,0],"shinR":[45,0,0],"footR":[-25,0,0],"thighL":[22,0,0],"shinL":[12,0,0],"footL":[25,0,0]}'
CROUCH='{"thighR":[-95,0,0],"shinR":[115,0,0],"footR":[-25,0,0],"thighL":[-80,0,8],"shinL":[100,0,0],"footL":[-20,0,0],"spine1":[18,0,0],"spine2":[12,0,0],"chest":[8,0,0]}'
HEAD='{"neck":[22,35,0],"head":[12,25,0],"clavR":[0,0,18],"clavL":[0,0,-10],"uarmR":[0,0,70],"uarmL":[0,0,-30]}'
TWIST='{"spine1":[-10,25,0],"spine2":[-8,20,10],"chest":[0,15,8],"thighR":[-50,0,-15],"shinR":[60,0,0]}'
q(){ node charstills.mjs "$@" 2>&1 | grep -v 'GPU stall' || true; }
q ${P}_walk "waist;feet" "$WALK"
q ${P}_crouch "waist;waistB;feet" "$CROUCH"
q ${P}_head "neck;face" "$HEAD"
q ${P}_twist "waist;waistB" "$TWIST"
python3 - "$P" <<'EOF'
import sys
from PIL import Image
P = sys.argv[1]
def sheet(out, names):
    ims = [Image.open(f'{P}_{n}.png') for n in names]
    o = Image.new('RGB', (sum(i.width for i in ims), max(i.height for i in ims))); x = 0
    for i in ims: o.paste(i, (x, 0)); x += i.width
    o.save(out)
sheet(f'{P}_s1.png', ['walk_waist', 'walk_feet', 'crouch_feet'])
sheet(f'{P}_s2.png', ['crouch_waist', 'crouch_waistB', 'twist_waist', 'twist_waistB'])
sheet(f'{P}_s3.png', ['head_neck', 'head_face'])
print('sheets:', f'{P}_s1.png {P}_s2.png {P}_s3.png')
EOF
