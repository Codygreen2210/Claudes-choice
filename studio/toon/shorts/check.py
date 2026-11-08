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
# quiet spots: any 0.4 s stretch far below the rest of the mix loses people (owner, 2026-11-07: "quiet spots that lose attention")
win, hop = int(0.4 * sr), int(0.1 * sr)
st = np.array([20 * np.log10(np.sqrt(np.mean(x[i:i + win] ** 2)) + 1e-9) for i in range(0, len(x) - win, hop)])
med = np.median(st); qs = [i * 0.1 for i, v in enumerate(st) if v < med - 8 and 0.2 < i * 0.1 < len(x) / sr - 0.6]
spots = []
for q in qs:
    if spots and q - spots[-1][1] <= 0.15: spots[-1][1] = q + 0.4
    else: spots.append([q, q + 0.4])
print('quiet spots:', 'none (ok)' if not spots else ', '.join(f'{a_:.1f}-{b_:.1f}s' for a_, b_ in spots) + '  (FILL THESE: a sound, a hit or keep the bed going)')
# sound effects: a new hit, whoosh or bit of foley at least every 1.5 s (the music alone doesn't hold attention)
if os.path.exists(f'{d}/mix.fx.wav'):
    import librosa
    fx, fsr = sf.read(f'{d}/mix.fx.wav'); fx = fx.mean(1) if fx.ndim > 1 else fx
    on = librosa.onset.onset_detect(y=fx.astype(np.float32), sr=fsr, units='time', backtrack=False, delta=0.08)
    on = np.concatenate([[0.0], on, [len(fx) / fsr]])
    lvl = lambda a_, b_: 20 * np.log10(np.sqrt(np.mean(fx[int(a_ * fsr):int(b_ * fsr)] ** 2)) + 1e-9)
    ref = np.median([lvl(i * 0.5, i * 0.5 + 0.5) for i in range(int(len(fx) / fsr / 0.5))])
    gaps = [(a_, b_) for a_, b_ in zip(on[:-1], on[1:]) if b_ - a_ > 1.5 and lvl(a_ + 0.1, b_) < ref - 6]   # a steady roar under it is fine
    print(f'sound effects: {len(on) - 2} hits, {len(on) / (len(fx) / fsr):.1f} a second;', 'no gaps over 1.5 s (ok)' if not gaps else
          'NOTHING NEW for ' + ', '.join(f'{a_:.1f}-{b_:.1f}s' for a_, b_ in gaps) + '  (add foley, a hit or a whoosh there)')
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
