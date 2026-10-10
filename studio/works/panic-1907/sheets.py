#!/usr/bin/env python3
"""sheets.py "0:.5,.6 4:.1,.2 ..."  -> contact sheets of chosen moments (scene:fractions), for looking at the film."""
import json, sys, subprocess, glob, os, shutil
from PIL import Image
T = json.load(open('timing.json'))['scenes']; out = sys.argv[2] if len(sys.argv) > 2 else '/home/claude/work/stills'
ts = []
for part in sys.argv[1].split():
    i, fr = part.split(':'); i = int(i)
    nxt = T[i + 1]['start'] - 0.45 if i + 1 < len(T) else T[i]['end'] + 4
    for f in fr.split(','): ts.append(round(T[i]['start'] + (nxt - T[i]['start']) * float(f), 2))
shutil.rmtree(out, ignore_errors=True)
subprocess.run(['node', '../../motion/render.mjs', 'film.html', '--size', '1920x1080', '--shots', ','.join(map(str, ts)), '--outdir', out], stdout=subprocess.DEVNULL, check=True)
fs = sorted(glob.glob(out + '/t*.png'))
for k in range(0, len(fs), 6):
    sh = Image.new('RGB', (1920, 540 * ((len(fs[k:k + 6]) + 1) // 2)))
    for j, f in enumerate(fs[k:k + 6]): sh.paste(Image.open(f).resize((960, 540)), ((j % 2) * 960, (j // 2) * 540))
    sh.save(f'{out}/sheet{k // 6}.jpg', quality=85)
print(ts)
