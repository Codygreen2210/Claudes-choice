#!/usr/bin/env python3
"""How to draw a serpent dragon: the sound. A slow koto-like pentatonic line over a low drone, and the drawing itself:
pencil scratches, ink glides and wet brush sweeps, each placed on the exact video frames where that stroke is drawn.
Stroke times come from the same recording and timeline the picture uses (read through Node), so nothing drifts."""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
from studio.instruments import synth as S  # noqa: E402

# the timing comes from serpent.js, the same pacing the page uses
JS = """
const TL = require('../../timelapse/timelapse.js'), D = require('./serpent.js')
const rec = D.build(TL), tl = TL.timeline(rec, D.timing(rec))
console.log(JSON.stringify({ dur: tl.duration, outro: tl.outro,
  steps: rec.steps.map(s => tl.videoTimeOf(s.t)),
  strokes: rec.strokes.map(s => [s.tool, tl.videoTimeOf(s.t0), tl.videoTimeOf(s.t1)]) }))
"""
T = json.loads(subprocess.check_output(['node', '-e', JS], cwd=HERE))
DUR = T['dur']
S.seed(9)
rng = np.random.default_rng(4)
music, pen = S.Bus(DUR), S.Bus(DUR)

# ---------------------------------------------------------------- music: A minor pentatonic, unhurried, 60 BPM
BPM = 60; beat = 60 / BPM; bar = 4 * beat
PENTA = [57, 60, 62, 64, 67, 69, 72, 74, 76]                        # A C D E G A C D E
roots = [45, 41, 43, 45]                                            # A, F, G, A under it
t, k = 0.0, 0
while t < DUR:
    r = roots[k % 4]
    music.add(t, S.hp(S.soft_pad([r + 12, r + 19, r + 24], bar, a=1.5, r=2.0, bright=1600), 150), 0.07)
    music.add(t, S.lp(S.sine(S.mtof(r), S.smp(bar)) * np.minimum(1, np.arange(S.smp(bar)) / S.SR / 0.8), 400), 0.08)
    if k >= 1 and t < DUR - T['outro']:
        # a koto-like phrase: a few plucks walking the scale, with space between them
        pos = int(rng.integers(3, 7))
        for b in range(4):
            if rng.random() < 0.7:
                pos = int(np.clip(pos + rng.choice([-2, -1, 1, 2]), 0, len(PENTA) - 1))
                music.add(t + b * beat + rng.uniform(0, 0.08), S.karplus(PENTA[pos], 2.2, 0.6, 0.997), 0.16, rng.uniform(-0.4, 0.4))
                if rng.random() < 0.3:                                 # a grace pluck just before
                    music.add(t + b * beat - 0.09, S.karplus(PENTA[max(0, pos - 1)], 0.6, 0.5, 0.99), 0.07, 0.2)
    t += bar; k += 1

# a bright chime as each step's title comes up
for i, st in enumerate(T['steps']):
    music.add(st, S.bell(84 + [0, 2, 4, 7][i % 4], 1.4), 0.05, 0.1)

# ---------------------------------------------------------------- the pen on paper
def scratch(dur, tool):
    n = max(S.smp(dur), 64); tq = np.arange(n) / S.SR
    wig = 0.6 + 0.4 * np.abs(np.sin(2 * np.pi * (5 + 4 * rng.random()) * tq + rng.random() * 6))   # the hand's rhythm
    env = np.clip(tq / 0.02, 0, 1) * np.clip((dur - tq) / 0.04, 0, 1) * wig
    if tool == 'pencil':
        return S.bp(S.noise(n), 2500, 9000) * env * 0.9
    if tool == 'ink':
        return S.bp(S.noise(n, 'pink'), 1200, 6000) * env * 0.6
    return S.lp(S.noise(n, 'pink'), 1500) * env                           # brush / fill: a soft wet swish

for tool, a, b in T['strokes']:
    if tool == 'erase':
        pen.add(a, S.bp(S.noise(S.smp(b - a)), 800, 4000) * np.abs(np.sin(np.linspace(0, 14 * np.pi, S.smp(b - a)))), 0.12, 0)
        continue
    if b - a < 0.01:
        continue
    g = {'pencil': 0.10, 'ink': 0.09, 'brush': 0.12, 'fill': 0.12}[tool]
    pen.add(a, scratch(b - a, tool), g, rng.uniform(-0.2, 0.2))

mix = S.hp(music.out(), 120) + pen.out() * 1.6
S.write(HERE / 'serpent.wav', S.master(mix, lufs=-16, fade=1.5))
print(f'serpent.wav: {DUR:.1f} s, {len(T["strokes"])} strokes voiced')
