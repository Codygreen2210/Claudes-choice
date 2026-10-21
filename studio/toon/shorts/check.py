#!/usr/bin/env python3
"""Quality checks for a built Short.  python3 check.py <work dir>
Prints: loudness line from the ears, voice steadiness (spread across lines), the loop seam, and writes grid.png (10 frames)."""
import json, os, subprocess, sys
import numpy as np, soundfile as sf
from PIL import Image

d = sys.argv[1]
t = json.load(open(f'{d}/times.json'))
for ln in open(f'{d}/ears.txt'):
    if 'loudness' in ln or ln.startswith('  - '):
        print('ears:', ln.rstrip())
x, sr = sf.read(f'{d}/mix.wav'); x = x.mean(1) if x.ndim > 1 else x
lv = [20 * np.log10(np.sqrt(np.mean(x[int(a * sr):int(b * sr)] ** 2))) for a, b in t['voice']]
spread = max(lv) - min(lv)
print(f'voice spread across lines: {spread:.1f} dB', '(ok)' if spread <= 2.5 else '(TOO UNEVEN, fix sfx/levels)')
dur = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f'{d}/pic.mp4']))
tmp = f'{d}/_chk'; os.makedirs(tmp, exist_ok=True)
grab = lambda ts, out, vf=None: subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-ss', str(ts), '-i', f'{d}/pic.mp4', '-frames:v', '1'] + (['-vf', vf] if vf else []) + [out])
grab(0, f'{tmp}/a.png'); grab(dur - 0.07, f'{tmp}/b.png')
seam = np.abs(np.asarray(Image.open(f'{tmp}/a.png'), float) - np.asarray(Image.open(f'{tmp}/b.png'), float)).mean()
print(f'loop seam diff: {seam:.1f}', '(ok)' if seam < 15 else '(JUMP at the loop, fix the last beat)')
g = Image.new('RGB', (216 * 5, 384 * 2))
for i, ts in enumerate(np.linspace(0.3, dur - 0.3, 10)):
    grab(ts, f'{tmp}/g{i}.png', 'scale=216:384'); g.paste(Image.open(f'{tmp}/g{i}.png'), ((i % 5) * 216, (i // 5) * 384))
g.save(f'{d}/grid.png'); print('frame grid:', f'{d}/grid.png')
