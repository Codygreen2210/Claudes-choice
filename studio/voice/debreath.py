#!/usr/bin/env python3
"""Take the breaths out of a finished narration: every low run between words (the inhale and the hiss around it, quieter
than -24 dB under the peak for over 90 ms) is cut down to a 35 ms join, and times.json is moved to match.
    python3 debreath.py DIR [--floor -24] [--min 0.09] [--keep 0.035]
DIR holds narration.wav + times.json; the originals are kept as narration_breath.wav / times_breath.json.
Owner, 2026-11-16: "take the breaths out of video"."""
import sys, os, json, shutil, argparse
import numpy as np, soundfile as sf
ap = argparse.ArgumentParser(); ap.add_argument('dir')
ap.add_argument('--floor', type=float, default=-24.0); ap.add_argument('--min', type=float, default=0.09); ap.add_argument('--keep', type=float, default=0.035)
a = ap.parse_args(); d = a.dir
wav, tj = os.path.join(d, 'narration.wav'), os.path.join(d, 'times.json')
if not os.path.exists(os.path.join(d, 'narration_breath.wav')): shutil.copy(wav, os.path.join(d, 'narration_breath.wav'))
if not os.path.exists(os.path.join(d, 'times_breath.json')): shutil.copy(tj, os.path.join(d, 'times_breath.json'))
y, sr = sf.read(os.path.join(d, 'narration_breath.wav')); T = json.load(open(os.path.join(d, 'times_breath.json')))
mono = y if y.ndim == 1 else y.mean(1)
h = int(0.01 * sr)                                                   # 10 ms RMS envelope
e = np.sqrt(np.convolve(mono ** 2, np.ones(h) / h, 'same')) + 1e-9
db = 20 * np.log10(e / e.max())
low = db < a.floor
n, keep, xf = len(mono), int(a.keep * sr), int(0.01 * sr)
cuts = []                                                            # (start, end) sample spans removed
i = 0
while i < n:
    if not low[i]: i += 1; continue
    j = i
    while j < n and low[j]: j += 1
    if j - i > a.min * sr and i > 0 and j < n:
        c0 = i + keep // 3; c1 = j - 2 * keep // 3                    # more room before the next word: soft starts (w, h, g) live there
        if c1 - c0 > xf: cuts.append((c0, c1))
    i = j
out, last = [], 0
for c0, c1 in cuts:
    out.append(y[last:c0 - xf])
    f = np.linspace(1, 0, xf); f = f[:, None] if y.ndim > 1 else f
    out.append(y[c0 - xf:c0] * f + y[c1 - xf:c1] * (1 - f))
    last = c1
out.append(y[last:]); z = np.concatenate(out)
def mv(t):                                                           # old time -> new time
    s = t * sr; r = 0
    for c0, c1 in cuts:
        if s >= c1: r += c1 - c0
        elif s > c0: r += s - c0
    return (s - r) / sr
starts = [mv(s) for s in T['starts']]; total = len(z) / sr
T2 = dict(T); T2['starts'] = starts; T2['durs'] = [b - s for s, b in zip(starts, starts[1:] + [total])]; T2['total'] = total
if 'voice' in T: T2['voice'] = [[mv(p), mv(q)] for p, q in T['voice']]
sf.write(wav, z, sr); json.dump(T2, open(tj, 'w'), indent=1)
print(f'cut {len(cuts)} breaths, {sum(c1 - c0 for c0, c1 in cuts) / sr:.2f} s gone: {T["total"]:.2f} s -> {total:.2f} s')
