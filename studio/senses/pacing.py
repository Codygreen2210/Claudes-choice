#!/usr/bin/env python3
"""pacing.py: does the music change with the story? Checks a score against its scene plan.

    python3 studio/senses/pacing.py music.wav plan.json [--out notes/]

plan.json is the list moods.Score.write() saves: [{t0, t1, mood, energy, bpm}, ...].
For each scene it measures loudness, how busy it is (onsets a second), brightness and tempo, then flags:
  - neighbouring scenes with different moods that measure almost the same (the music didn't really change);
  - a plan where the energy goes up but the music doesn't get louder or busier (the shape isn't heard);
  - a long film that sits on too few moods.
Writes <name>.pacing.txt and .png next to the other notes.
"""
import json, os, sys, warnings
warnings.filterwarnings('ignore')
import numpy as np, soundfile as sf, librosa, pyloudnorm as pyln

args = sys.argv[1:]; out = 'notes'
if '--out' in args: k = args.index('--out'); out = args[k + 1]; del args[k:k + 2]
wav, planf = args[:2]; os.makedirs(out, exist_ok=True)
y, sr = sf.read(wav); mono = y.mean(1) if y.ndim > 1 else y
plan = json.load(open(planf)); meter = pyln.Meter(sr)
rows = []
for p in plan:
    a, b = int(p['t0'] * sr), int(min(p['t1'], len(mono) / sr) * sr)
    seg = mono[a:b]
    if len(seg) < sr: continue
    lufs = meter.integrated_loudness(np.stack([seg, seg], 1)) if len(seg) > sr * 0.5 else -70
    on = librosa.onset.onset_detect(y=seg.astype(np.float32), sr=sr, units='time')
    tempo = float(np.atleast_1d(librosa.beat.beat_track(y=seg.astype(np.float32), sr=sr)[0])[0])
    cent = float(np.mean(librosa.feature.spectral_centroid(y=seg.astype(np.float32), sr=sr)))
    rows.append({**p, 'lufs': round(float(lufs), 1), 'onsets_s': round(len(on) / (len(seg) / sr), 2), 'tempo': round(tempo), 'bright': round(cent)})

flags = []
for r0, r1 in zip(rows, rows[1:]):
    if r0['mood'] != r1['mood'] and abs(r0['lufs'] - r1['lufs']) < 1.5 and abs(r0['onsets_s'] - r1['onsets_s']) < 0.5 and abs(r0['bright'] - r1['bright']) / max(r0['bright'], 1) < 0.12:
        flags.append(f"{r0['t0']:.0f}-{r1['t1']:.0f}s: '{r0['mood']}' into '{r1['mood']}' measures almost the same; the change may not be heard")
if len(rows) >= 4:
    e = np.array([r['energy'] for r in rows]); drive = np.array([r['lufs'] for r in rows]) + 4 * np.array([r['onsets_s'] for r in rows])
    if np.std(e) > 0.1:
        rc = float(np.corrcoef(np.argsort(np.argsort(e)), np.argsort(np.argsort(drive)))[0, 1])
        if rc < 0.3: flags.append(f'the energy plan and what is heard do not line up (rank correlation {rc:.2f}); high-energy scenes should be louder or busier')
    span = rows[-1]['t1'] - rows[0]['t0']
    if span > 240 and len({r['mood'] for r in rows}) < 3: flags.append(f'{span / 60:.0f} minutes on {len({r["mood"] for r in rows})} mood(s); it will feel the same all the way through')
    if np.std([r['onsets_s'] for r in rows]) < 0.4 and np.std([r['lufs'] for r in rows]) < 1.5: flags.append('every scene measures alike in loudness and busyness: flat')

name = os.path.splitext(os.path.basename(wav))[0]
lines = [f'{name}: pacing against {len(rows)} scenes', '', f"{'time':>11}  {'mood':9} {'energy':>6} {'bpm plan':>8} {'tempo':>6} {'LUFS':>6} {'onsets/s':>8} {'bright':>7}"]
for r in rows: lines.append(f"{r['t0']:5.0f}-{r['t1']:<5.0f} {r['mood']:9} {r['energy']:6.2f} {r['bpm']:8d} {r['tempo']:6d} {r['lufs']:6.1f} {r['onsets_s']:8.2f} {r['bright']:7d}")
lines += ['', 'listen out for:'] + ([f'  - {f}' for f in flags] or ['  - nothing flagged'])
open(os.path.join(out, name + '.pacing.txt'), 'w').write('\n'.join(lines) + '\n'); print('\n'.join(lines))

import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
fig, ax = plt.subplots(3, 1, figsize=(12, 6), sharex=True, facecolor='#111')
cols = {'wonder': '#7fb3d5', 'calm': '#a9cce3', 'mystery': '#8e7cc3', 'dread': '#4a235a', 'tension': '#e67e22', 'action': '#e74c3c', 'march': '#b03a2e', 'grief': '#566573', 'triumph': '#f4d03f', 'jaunty': '#58d68d'}
for i, (k, lab) in enumerate((('lufs', 'loudness (LUFS)'), ('onsets_s', 'onsets a second'), ('energy', 'planned energy'))):
    a = ax[i]; a.set_facecolor('#111'); a.tick_params(colors='#999'); a.set_ylabel(lab, color='#ccc', fontsize=8)
    for r in rows: a.barh(0, 0); a.fill_between([r['t0'], r['t1']], [r[k], r[k]], color=cols.get(r['mood'], '#888'), alpha=0.85, step='pre')
    if i == 0:
        for r in rows: a.text((r['t0'] + r['t1']) / 2, max(x['lufs'] for x in rows) + 0.5, r['mood'], color='#eee', fontsize=7, ha='center')
ax[-1].set_xlabel('seconds', color='#ccc'); plt.tight_layout(); fig.savefig(os.path.join(out, name + '.pacing.png'), dpi=110)
