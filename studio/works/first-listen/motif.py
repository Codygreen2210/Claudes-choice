"""Motif generator for First Listen: a genome -> a 4-bar melody in A major over a held Amaj9."""
import random
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from studio.instruments import synth as S, theory as T

BPM = 84
BEAT = 60 / BPM
SCALE = T.scale('A', 'major', octave=4, octaves=2)      # A4..A6
SPACE = {'contour': ['arch', 'rise', 'fall', 'wave', 'call-answer'], 'leap': [0.0, 1.0], 'density': [0.35, 0.85],
         'range_n': [5, 11], 'rhythm': ['even', 'dotted', 'sparse', 'syncopated'], 'seed': 'int'}


def melody(g, bars=4):
    rnd = random.Random(g['seed'])
    steps = {'even': [1, 1, 1, 1], 'dotted': [1.5, 0.5, 1, 1], 'sparse': [2, 1, 1], 'syncopated': [0.75, 0.75, 0.5, 1, 1]}[g['rhythm']]
    ev, t = [], 0.0
    n_total = bars * 4
    rng_n = int(g['range_n'])
    idx = 2
    while t < n_total - 0.5:
        for d in steps:
            if t >= n_total - 0.5:
                break
            p = t / n_total
            shape = {'arch': 1 - abs(2 * p - 1), 'rise': p, 'fall': 1 - p, 'wave': 0.5 + 0.5 * __import__('math').sin(p * 6.28 * 2),
                     'call-answer': (p * 2) % 1 if p < 0.5 else 1 - (p * 2) % 1}[g['contour']]
            target = shape * rng_n
            jump = rnd.choice([-2, -1, 1, 2]) + (rnd.choice([-4, 4]) if rnd.random() < g['leap'] * 0.4 else 0)
            idx = int(round(0.6 * target + 0.4 * (idx + jump)))
            idx = max(0, min(len(SCALE) - 1, idx))
            if rnd.random() < g['density'] or not ev:
                ev.append((t * BEAT, SCALE[idx], d * BEAT))
            t += d
    # land on the root or the third at the end
    ev.append((n_total * BEAT - 0.01, rnd.choice([SCALE[0], SCALE[2], SCALE[7]]), 2 * BEAT))
    return ev


def make(g, seconds):
    ev = melody(g)
    dur = 4 * 4 * BEAT + 2.5
    b = S.Bus(dur)
    for t, m, d in ev:
        b.add(t + 0.1, S.epiano(m, max(d * 1.6, 0.8), 0.7), 0.35, pan=(m - 76) / 30)
    b.add(0.1, S.soft_pad(T.chord('Amaj9', 3), dur - 1.5, a=0.8, r=1.2, bright=1400), 0.3)
    return b.out()
