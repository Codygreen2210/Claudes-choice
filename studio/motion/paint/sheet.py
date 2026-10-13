#!/usr/bin/env python3
"""sheet.py: render frames of a film page at given times and lay them out as phone-size contact sheets.
usage: sheet.py page.html outdir t1,t2,... | --every 4 [--from a --to b]
Prints page errors and missing cue words (window.__missing)."""
import sys, os, subprocess, glob
from PIL import Image, ImageDraw
page, out = sys.argv[1], sys.argv[2]
args = sys.argv[3:]
def opt(n, d=None):
    return args[args.index(n) + 1] if n in args else d
if args and args[0] != '--every':
    times = [float(x) for x in args[0].split(',')]
else:
    import json, re
    every = float(opt('--every', 4)); a = float(opt('--from', 0)); b = opt('--to')
    if b is None:
        tm = os.path.join(os.path.dirname(page), 'timing.json'); b = json.load(open(tm))['total']
    b = float(b); times = []; t = a
    while t < b: times.append(round(t, 2)); t += every
os.makedirs(out, exist_ok=True)
for f in glob.glob(os.path.join(out, 't*.png')): os.remove(f)
root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'render.mjs')
r = subprocess.run(['node', root, page, '--size', '1920x1080', '--shots', ','.join(map(str, times)), '--outdir', out], capture_output=True, text=True)
for line in (r.stdout + r.stderr).splitlines():
    if any(k in line.lower() for k in ('exception', 'error', 'missing')): print(line)
fs = sorted(glob.glob(os.path.join(out, 't*.png')))
per = 12; tw, th = 480, 270
for p in range(0, len(fs), per):
    chunk = fs[p:p + per]; sh = Image.new('RGB', (tw * 4, th * 3), 'black'); d = ImageDraw.Draw(sh)
    for i, f in enumerate(chunk):
        im = Image.open(f).resize((tw, th)); x, y = (i % 4) * tw, (i // 4) * th; sh.paste(im, (x, y))
        d.text((x + 6, y + 4), os.path.basename(f)[1:-4], fill=(255, 255, 0))
    sh.save(os.path.join(out, f'sheet{p // per:02d}.png'))
print(len(fs), 'frames,', (len(fs) + per - 1) // per, 'sheets in', out)
