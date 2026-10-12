#!/usr/bin/env python3
"""The studio sampler: 90 seconds that walks through six moods with library sounds on top, so the moods engine
and the sound library can be heard together. Writes music.wav, fx.wav, final.wav, plan.json and sampler.mp4."""
import os, sys, subprocess
import numpy as np, soundfile as sf, pyloudnorm as pyln
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..', '..', '..')
sys.path.insert(0, ROOT)
from studio.instruments import synth as S
from studio.instruments.moods import Score, MOODS
from studio.sfx import foley as F
os.chdir(HERE)

L = 15.0
SCENES = [('wonder', 0.45, 'swell', 'a frozen coast at dawn',               [('bed', 'wind', -6)]),
          ('mystery', 0.45, 'swell', 'a coded message, a locked room',     [('seq', 'clock', -2), ('bed', 'crickets', -10)]),
          ('tension', 0.75, 'swell', 'the plan is set; the clock runs',    [('seq', 'heart', 0, {'gap0': 0.9, 'gap1': 0.5})]),
          ('action', 0.95, 'hit', 'the attack',                            [('seq', 'volley', -6, {'per_s': 4}), ('hits', 'cannon', -2), ('bed', 'panic', -10)]),
          ('grief', 0.35, 'soft', 'the morning after',                     [('bed', 'rain', -8), ('hit1', 'toll', -6)]),
          ('triumph', 0.9, 'hit', 'the news reaches home',                 [('bed', 'cheer', -6)])]
DUR = L * len(SCENES) + 3
sc = Score(DUR, key='E'); fx = F.Track(DUR, seed=3)
for i, (mood, e, enter, what, sfx) in enumerate(SCENES):
    t0, t1 = i * L, (i + 1) * L + (3 if i == len(SCENES) - 1 else 0)
    sc.scene(t0, t1, mood, e, enter=enter)
    for s in sfx:
        kind, name, db = s[:3]; kw = s[3] if len(s) > 3 else {}
        if kind == 'bed': fx.bed(name, t0, t1, db, fin=1.0, fout=1.0, **kw)
        elif kind == 'seq': fx.seq(name, t0 + 0.5, t1 - 0.5, db, **kw)
        elif kind == 'hits':
            for t in np.arange(t0 + 1.0, t1 - 1.0, 2.7): fx.hit(name, t + np.random.uniform(0, 0.6), db, pan=np.random.uniform(-0.7, 0.7))
        elif kind == 'hit1': fx.hit(name, t0 + 2.0, db)
plan = sc.write('music.wav', 'plan.json')
f = fx.out(); n = S.smp(DUR); f = f[:, :n] * np.clip((DUR - np.arange(n) / S.SR) / 3, 0, 1)
f = S.eq(S.hp(f, 60), [('lowshelf', 130, -5.0, 0.7), ('peak', 350, -2.0, 1.0), ('highshelf', 5000, 4.0, 0.7)])   # sounds sit above the music's low end
S.write('fx.wav', S.limiter(f * 1.0, 0.7))
m, _ = sf.read('music.wav'); fxw, _ = sf.read('fx.wav'); k = min(len(m), len(fxw))
meter = pyln.Meter(S.SR); mix = m[:k] + fxw[:k] * 0.9
S.write('final.wav', S.master(mix.T, lufs=-14.0, fade=0, ceiling=0.86))
for w in ('music', 'fx', 'final'): subprocess.run([sys.executable, os.path.join(ROOT, 'studio/senses/listen.py'), w + '.wav', '--out', 'notes/'], stdout=subprocess.DEVNULL)
subprocess.run([sys.executable, os.path.join(ROOT, 'studio/senses/pacing.py'), 'music.wav', 'plan.json', '--out', 'notes/'])

# the video: one card a scene, so the moods can be heard against their names
from PIL import Image, ImageDraw, ImageFont
fdir = os.path.join(ROOT, 'studio/works/ponzi/fonts'); big = ImageFont.truetype(os.path.join(fdir, 'Playfair.ttf'), 120); it = ImageFont.truetype(os.path.join(fdir, 'Playfair-Italic.ttf'), 40); sm = ImageFont.truetype(os.path.join(fdir, 'Playfair-Italic.ttf'), 30)
lst = []
for i, (mood, e, enter, what, sfx) in enumerate(SCENES):
    im = Image.new('RGB', (1280, 720), '#14110e'); d = ImageDraw.Draw(im)
    d.text((640, 250), mood.upper(), fill='#f4ead2', font=big, anchor='mm')
    d.text((640, 360), what, fill='#c9973a', font=it, anchor='mm')
    d.text((640, 430), f"{MOODS[mood][0]} beats a minute  ·  {MOODS[mood][1]}  ·  energy {e:.2f}", fill='#9a8f80', font=sm, anchor='mm')
    d.text((640, 480), 'sounds: ' + ', '.join(s[1] for s in sfx), fill='#9a8f80', font=sm, anchor='mm')
    d.rectangle([340, 560, 340 + int(600 * e), 580], fill='#e2452f'); d.rectangle([340, 560, 940, 580], outline='#5a5048')
    p = f'_c{i}.png'; im.save(p); lst.append((p, L + (3 if i == len(SCENES) - 1 else 0)))
open('_l.txt', 'w').write(''.join(f"file '{p}'\nduration {d}\n" for p, d in lst) + f"file '{lst[-1][0]}'\n")
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', '_l.txt', '-i', 'final.wav', '-vf', 'fps=30,format=yuv420p', '-c:v', 'libx264', '-crf', '22', '-c:a', 'aac', '-b:a', '192k', '-shortest', '/home/claude/work/studio-sampler.mp4'], check=True)
for p, _ in lst: os.remove(p)
os.remove('_l.txt')
print('sampler done', round(DUR, 1), 's')
