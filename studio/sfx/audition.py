#!/usr/bin/env python3
"""audition.py: hear every sound on its own before it goes in a film (the sound version of a model sheet).

    python3 studio/sfx/audition.py            # every sound in the library
    python3 studio/sfx/audition.py cannon roar # just these

Writes, in studio/sfx/auditions/:
  <name>.wav     the sound alone (beds 12 s, sequences 6 s)
  sheet.png      a spectrogram tile per sound with its numbers, to look at
  reel.wav       all of them in a row, which also goes through the studio's ears (listen.py)
  reel.mp4       the reel with a name card for each sound, for Cody to listen to
and rewrites studio/sfx/CATALOG.md. Prints a flag for anything clipped, offset, late to start or empty.
"""
import os, sys, subprocess, json
import numpy as np, soundfile as sf
from scipy.signal import resample_poly
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..', '..')
sys.path.insert(0, ROOT)
from studio.sfx import foley as F
from studio.instruments import synth as S

OUT = os.path.join(HERE, 'auditions'); os.makedirs(OUT, exist_ok=True)
names = sys.argv[1:] or list(F.REG)
db = lambda v: 20 * np.log10(max(v, 1e-9))
rows, clips = [], []
for nm in names:
    y = F.render(nm); y = np.nan_to_num(y)
    sf.write(os.path.join(OUT, nm + '.wav'), y.T.astype(np.float32), S.SR, subtype='PCM_16')
    mono = y.mean(0); peak = np.abs(y).max(); tp = np.abs(resample_poly(y, 4, 1, axis=1)).max()
    spec = np.abs(np.fft.rfft(mono)); fr = np.fft.rfftfreq(len(mono), 1 / S.SR); cent = float((spec * fr).sum() / max(spec.sum(), 1e-9))
    start = int(np.argmax(np.abs(mono) > 0.02 * max(peak, 1e-9))) / S.SR
    flags = []
    if not np.isfinite(y).all() or peak < 1e-4: flags.append('EMPTY')
    if db(tp) > -1.0: flags.append(f'true peak {db(tp):.1f} dBTP')
    if abs(mono.mean()) > 0.01: flags.append('DC offset')
    if F.REG[nm]['kind'] == 'hit' and nm != 'riser' and start > 0.05: flags.append(f'starts late ({start * 1000:.0f} ms)')
    mid = float((spec[fr > 300] ** 2).sum() / max((spec ** 2).sum(), 1e-12))
    if mid < 0.08: flags.append(f'phone speakers will barely hear it ({mid * 100:.0f}% of energy above 300 Hz)')
    low = float((spec[(fr > 30) & (fr < 150)] ** 2).sum() / max((spec ** 2).sum(), 1e-12))
    if nm in getattr(F, 'WEIGHTY', ()) and low < 0.12: flags.append(f'thin: only {low * 100:.0f}% of its energy is below 150 Hz for something this heavy')
    if cent < 60 or cent > 11000: flags.append(f'odd brightness {cent:.0f} Hz')
    rows.append({'name': nm, 'kind': F.REG[nm]['kind'], 'cat': F.REG[nm]['cat'], 'dur': y.shape[1] / S.SR, 'peak': db(peak), 'tp': db(tp),
                 'rms': db(np.sqrt(np.mean(mono ** 2))), 'cent': cent, 'flags': flags})
    clips.append((nm, y))
    print(f"{nm:12s} {F.REG[nm]['kind']:4s} {y.shape[1] / S.SR:5.1f}s  peak {db(peak):6.1f}  tp {db(tp):6.1f}  rms {db(np.sqrt(np.mean(mono ** 2))):6.1f}  bright {cent:6.0f} Hz  {'  '.join(flags)}")

# the sheet
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
cols = 5; rws = (len(clips) + cols - 1) // cols
fig, axs = plt.subplots(rws, cols, figsize=(cols * 3.6, rws * 2.4), facecolor='#111')
for ax in np.atleast_1d(axs).ravel(): ax.axis('off')
for ax, (nm, y), r in zip(np.atleast_1d(axs).ravel(), clips, rows):
    ax.specgram(y.mean(0) + 1e-9, NFFT=1024, Fs=S.SR, noverlap=768, cmap='magma', vmin=-120)
    ax.set_ylim(0, 12000); ax.axis('on'); ax.tick_params(colors='#777', labelsize=6)
    ax.set_title(f"{nm}  ({r['kind']})\npeak {r['peak']:.0f} dB  bright {r['cent']:.0f} Hz" + ('  ⚑ ' + '; '.join(r['flags']) if r['flags'] else ''), color='#f0e6d0' if not r['flags'] else '#ff7b5c', fontsize=7)
plt.tight_layout(); fig.savefig(os.path.join(OUT, 'sheet.png'), dpi=110); plt.close(fig)

# the reel, with name cards
from PIL import Image, ImageDraw, ImageFont
font = os.path.join(ROOT, 'studio', 'works', 'ponzi', 'fonts', 'Playfair.ttf'); fontI = os.path.join(ROOT, 'studio', 'works', 'ponzi', 'fonts', 'Playfair-Italic.ttf')
gap = np.zeros((2, S.smp(0.7))); parts, cards = [], []
for i, ((nm, y), r) in enumerate(zip(clips, rows)):
    seg = np.concatenate([y, gap], 1); parts.append(seg)
    im = Image.new('RGB', (1280, 720), '#14110e'); d = ImageDraw.Draw(im)
    d.text((640, 300), nm.replace('_', ' '), fill='#f4ead2', font=ImageFont.truetype(font, 96), anchor='mm')
    d.text((640, 400), F.REG[nm]['desc'], fill='#c9973a', font=ImageFont.truetype(fontI, 34), anchor='mm')
    d.text((640, 640), f"{r['cat']}  ·  {r['kind']}  ·  {i + 1} of {len(clips)}", fill='#7d7368', font=ImageFont.truetype(fontI, 26), anchor='mm')
    p = os.path.join(OUT, f'_card{i:03d}.png'); im.save(p); cards.append((p, seg.shape[1] / S.SR))
reel = np.concatenate(parts, 1); reel = reel / max(1.0, np.abs(reel).max() / 0.85)
sf.write(os.path.join(OUT, 'reel.wav'), reel.T.astype(np.float32), S.SR, subtype='PCM_16')
lst = os.path.join(OUT, '_cards.txt')
with open(lst, 'w') as fh:
    for p, d in cards: fh.write(f"file '{p}'\nduration {d:.3f}\n")
    fh.write(f"file '{cards[-1][0]}'\n")
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', lst, '-i', os.path.join(OUT, 'reel.wav'), '-vf', 'fps=30,format=yuv420p',
                '-c:v', 'libx264', '-crf', '24', '-c:a', 'aac', '-b:a', '160k', '-shortest', os.path.join(OUT, 'reel.mp4')], check=True)
for p, _ in cards: os.remove(p)
os.remove(lst)
subprocess.run([sys.executable, os.path.join(ROOT, 'studio', 'senses', 'listen.py'), os.path.join(OUT, 'reel.wav'), '--out', OUT], check=False, stdout=subprocess.DEVNULL)

# the catalog: always the whole library, whatever was auditioned
cats = {}
for nm, e in F.REG.items(): cats.setdefault(e['cat'], []).append((nm, e))
md = ['# Sound effects catalog', '', 'Everything in `studio/sfx/foley.py`, built from scratch. Rewritten by `audition.py`; do not edit by hand.', '',
      'Use: `fx = F.Track(dur)` then `fx.hit(name, t)`, `fx.bed(name, t0, t1)`, `fx.seq(name, t0, t1)`.', '']
for c in sorted(cats):
    md += [f'## {c}', '', '| sound | kind | what it is |', '|---|---|---|'] + [f"| `{nm}` | {e['kind']} | {e['desc']} |" for nm, e in sorted(cats[c])] + ['']
open(os.path.join(HERE, 'CATALOG.md'), 'w').write('\n'.join(md))
json.dump(rows, open(os.path.join(OUT, 'audition.json'), 'w'), indent=1)
print(len(clips), 'sounds;', sum(1 for r in rows if r['flags']), 'flagged; sheet, reel and catalog written')
