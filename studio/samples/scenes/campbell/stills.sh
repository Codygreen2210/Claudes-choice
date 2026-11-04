# stills.sh name "t1,t2,..." [w h] -> sheet
mkdir -p ${SDIR:-/tmp/stills/campbell}
cd "$(dirname "$0")/../../web" && PAGE=${PAGE:-campbell_mh.html} timeout 900 node qstills.mjs ${SDIR:-/tmp/stills/campbell}/$1 $2 ${3:-540} ${4:-960} 2>&1 | grep -v "^\s*$" | head -20
cd ${SDIR:-/tmp/stills/campbell} && python3 -c "
from PIL import Image; import sys
ts='$2'.split(','); n=len(ts); c=min(7,n); r=(n+c-1)//c
ims=[Image.open(f'$1_{t}.png').resize((270,480)) for t in ts]
W=Image.new('RGB',(270*c,480*r))
for i,im in enumerate(ims): W.paste(im,((i%c)*270,(i//c)*480))
W.save('$1_sheet.png')"
