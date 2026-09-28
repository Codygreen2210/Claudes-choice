#!/usr/bin/env python3
"""How to draw a dragon: the sound. A slow, warm electric-piano loop under the lesson, and the drawing itself:
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

# the timing must match dragon.html's TIMING
JS = """
const TL = require('../../timelapse/timelapse.js'), D = require('./dragon.js')
const rec = D.build(TL), tl = TL.timeline(rec, { speed: 2.4, holdStep: 1.1, intro: 2.6, outro: 3.4 })
console.log(JSON.stringify({ dur: tl.duration, outro: tl.outro,
  steps: rec.steps.map(s => tl.videoTimeOf(s.t)),
  strokes: rec.strokes.map(s => [s.tool, tl.videoTimeOf(s.t0), tl.videoTimeOf(s.t1)]) }))
"""
T = json.loads(subprocess.check_output(['node', '-e', JS], cwd=HERE))
DUR = T['dur']
S.seed(9)
rng = np.random.default_rng(4)
music, pen = S.Bus(DUR), S.Bus(DUR)

# ---------------------------------------------------------------- music: Fmaj7 - Em7 - Dm7 - Cmaj7, 76 BPM
BPM = 76; beat = 60 / BPM; bar = 4 * beat
chords = [[53, 57, 60, 64], [52, 55, 59, 62], [50, 53, 57, 60], [48, 52, 55, 59]]
melody = [72, 69, 67, 64, 71, 67, 64, 62, 69, 65, 64, 60, 67, 64, 62, 59]          # a lazy falling line, one per beat
t, k = 0.0, 0
while t < DUR:
    ch = chords[k % 4]
    music.add(t, S.hp(S.soft_pad([m + 12 for m in ch[1:]], bar, a=0.8, r=1.2, bright=2400), 300), 0.06)
    for i, m in enumerate(ch):                                          # a soft rolled chord on beat 1
        music.add(t + i * 0.03, S.epiano(m, 2.4, 0.45), 0.10, -0.3 + 0.2 * i)
    music.add(t + 2 * beat, S.epiano(ch[0] - 12, 1.8, 0.4), 0.07)
    if k >= 1 and t < DUR - T['outro']:                                  # melody enters after the title card
        for b in range(4):
            if rng.random() < 0.8:
                music.add(t + b * beat + (0.04 if b % 2 else 0), S.epiano(melody[(k * 4 + b) % 16], 1.3, 0.5), 0.07, 0.25)
    t += bar; k += 1
# a gentle brushed-hat pulse once the drawing starts
t = T['steps'][0]
while t < DUR - T['outro']:
    music.add(t, S.hp(S.noise(S.smp(0.05)) * np.exp(-np.arange(S.smp(0.05)) / S.SR / 0.012), 6000), 0.03, 0.4)
    t += beat / 2

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
S.write(HERE / 'dragon.wav', S.master(mix, lufs=-16, fade=1.5))
print(f'dragon.wav: {DUR:.1f} s, {len(T["strokes"])} strokes voiced')
