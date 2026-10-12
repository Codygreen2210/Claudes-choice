#!/usr/bin/env python3
"""Honey: final true-peak pass on the mix, and a check that the bed survives.

LaunchReel's mixer ends on `alimiter=limit=0.95`, which left the mix at
-0.9 dBTP — over the house limit of -1, and liable to distort once a platform
re-encodes it to AAC. synth.limiter is true-peak aware (4x oversampled), so the
ceiling is set there instead.

It also reports how far the music ducks under the voice, because a bed that
disappears is a buried part, which is its own flag.

    python3 finish.py    ->  mix.wav (in place)
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'studio', 'instruments'))
sys.path.insert(0, '/home/claude/shims')

import synth as S          # noqa: E402
import soundfile as sf     # noqa: E402

MIX = os.path.join(HERE, 'mix.wav')

x, sr = sf.read(MIX, always_2d=True)
y = S.limiter(x.T, ceiling=0.84)          # ≈ -1.5 dBTP

up = np.stack([S.sg.resample_poly(y[c], 4, 1) for c in range(2)]) if hasattr(S, 'sg') else None
if up is None:
    from scipy import signal as sg
    up = np.stack([sg.resample_poly(y[c], 4, 1) for c in range(2)])
tp = 20 * np.log10(np.max(np.abs(up)) + 1e-12)

S.write(MIX, y, sr)

# how far does the bed duck?
lines = json.load(open(os.path.join(HERE, 'lines.json')))['lines']
score, _ = sf.read(os.path.join(HERE, 'score.wav'), always_2d=True)
m = y.mean(axis=0)


def rms_db(a):
    return 20 * np.log10(np.sqrt(np.mean(a ** 2)) + 1e-12)


speech, gaps = [], []
cur = 0.0
for ln in lines:
    if ln['start'] - cur > 0.25:
        gaps.append((cur, ln['start']))
    speech.append((ln['start'], ln['end']))
    cur = ln['end']

sp = np.concatenate([m[S.smp(a):S.smp(b)] for a, b in speech])
gp = np.concatenate([m[S.smp(a):S.smp(b)] for a, b in gaps]) if gaps else np.zeros(1)

print(f'mix.wav true peak {tp:+.2f} dBTP (house limit -1.0)')
print(f'under speech {rms_db(sp):.1f} dB | in the gaps {rms_db(gp):.1f} dB '
      f'| the bed comes back up {rms_db(gp) - rms_db(sp):+.1f} dB')
