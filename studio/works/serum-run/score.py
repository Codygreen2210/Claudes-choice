#!/usr/bin/env python3
"""score.py: the music and sound for The Serum Run, written against the narration's own timing.

Reads timing.json (from film_voice.py), writes music.wav and fx.wav.
A minor at 60 beats a minute. The trail runs on wind, paws and harness bells; the town on celesta and low strings;
it turns to A major when the serum comes in, and again under the statue.
"""
import json, re, sys, os
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
from studio.instruments import synth as S

TM = json.load(open('timing.json')); SC = TM['scenes']; DUR = TM['total']
norm = lambda s: re.sub(r'[^a-z0-9 ]', '', s.lower()).strip()
NW = [[norm(w['w']) for w in s['words']] for s in SC]
def q(i, phrase):
    p = norm(phrase).split()
    for k in range(len(NW[i]) - len(p) + 1):
        if NW[i][k:k + len(p)] == p: return SC[i]['words'][k]['s']
    raise SystemExit(f'cue not found: scene {i} "{phrase}"')
V = [0.0] + [s['start'] - 0.45 for s in SC[1:]] + [DUR]          # when each scene's picture starts

S.seed(1925)
rng = np.random.default_rng(1925)
mus = S.Bus(DUR, tail=6); low = S.Bus(DUR, tail=6); fx = S.Bus(DUR, tail=4)
_cache = {}
def inst(prog, m, dur, vel):
    k = (prog, m, round(dur, 2), vel)
    if dur > 5: return S.sfhit(int(m), program=prog, bank=0, channel=0, vel=int(vel), dur=dur + 0.6)      # long notes are one-offs: keeping them ran the machine out of memory
    if k not in _cache: _cache[k] = S.sfhit(int(m), program=prog, bank=0, channel=0, vel=int(vel), dur=dur + 0.6)
    return _cache[k]
PIANO, STR, TREM, CELLO, BASS, PIZZ, HARP, TIMP, BELL, KAL = 0, 48, 44, 42, 43, 45, 46, 47, 14, 108
def kal(t, m, vel=80, g=1.0, pan=0.1): mus.add(t, inst(KAL, m, 1.2, vel), g * 1.6, pan)
def piano(t, m, dur=2.5, vel=70, g=1.0, pan=0.0): mus.add(t, inst(PIANO, m, dur, vel), g * 2.2, pan)
def strings(t, notes, dur, vel=60, g=1.0, prog=STR, swell=1.2):
    for j, m in enumerate(notes):
        y = inst(prog, m, dur, vel).copy(); n = y.shape[1]; e = np.minimum(1, np.arange(n) / (swell * S.SR)) ** 1.5
        (low if m < 50 else mus).add(t, y * e, g * 1.5, (-0.3, 0.2, -0.1, 0.3)[j % 4])
def cello(t, m, dur, vel=70, g=1.0): low.add(t, inst(CELLO, m, dur, vel), g * 0.9, 0.15)
def pizz(t, m, vel=80, g=1.0): low.add(t, inst(PIZZ, m, 0.6, vel), g * 0.8, -0.1)
def harp(t, m, vel=70, g=1.0): mus.add(t, inst(HARP, m, 2.0, vel), g * 1.4, 0.25)

Em, C, Am, B, G, D, E = (52, 59, 64, 67), (48, 55, 60, 64), (45, 52, 57, 60), (47, 54, 59, 63), (43, 50, 55, 59), (50, 57, 62, 66), (52, 59, 64, 68)
PENT = [64, 67, 69, 71, 74, 76]
grid = lambda t: float(np.ceil(t))                                # next whole second
def bars(t0, t1): return np.arange(grid(t0), t1 - 0.5, 4.0)
def arp(t, ch, vel=58, g=1.0, step=1.0, shape=(0, 1, 2, 3)):
    for k, i in enumerate(shape): piano(t + k * step, ch[i] + 12, 3.0, vel + (4 if k == 0 else -4 * (k % 2)) + rng.integers(-3, 4), g, -0.15 + 0.1 * k)

# ---------------------------------------------------------------- sounds
def tick(t, hi=True, g=1.0):
    n = S.smp(0.09); x = np.arange(n) / S.SR
    y = S.bp(S.noise(n), 1800, 5200) * np.exp(-x / 0.006) * 0.8 + np.sin(2 * np.pi * (1250 if hi else 930) * x) * np.exp(-x / 0.018) * 0.6
    fx.add(t, y, 0.05 * g, -0.2)
def clack(t, g=1.0, f=420):
    n = S.smp(0.16); x = np.arange(n) / S.SR
    fx.add(t, S.bp(S.noise(n), 900, 4200) * np.exp(-x / 0.012) + np.sin(2 * np.pi * f * x) * np.exp(-x / 0.03) * 0.7, 0.10 * g, 0.3)
def thud(t, g=1.0, f=70):
    n = S.smp(0.5); x = np.arange(n) / S.SR
    fx.add(t, np.sin(2 * np.pi * f * (1 + 0.8 * np.exp(-x / 0.02)) * x) * np.exp(-x / 0.12) + S.lp(S.noise(n), 900) * np.exp(-x / 0.03) * 0.5, 0.22 * g, 0.0)
def clink(t, m=96, g=1.0, pan=0.0): fx.add(t, S.bell(m, 0.5, ratio=3.7, idx=1.4, dec=0.14), 0.035 * g, pan)
def swish(t, g=1.0, dur=0.25): fx.add(t, S.whoosh(dur, 900, 3800, 0.9), 0.05 * g, 0.1)
def scratch(t0, dur, g=1.0):
    n = S.smp(dur); x = np.arange(n) / S.SR
    am = 0.5 + 0.5 * np.sin(2 * np.pi * (9 + 3 * np.sin(x * 5)) * x)
    fx.add(t0, S.bp(S.noise(n), 2200, 6500) * am * np.clip(x / 0.03, 0, 1) * np.clip((dur - x) / 0.05, 0, 1), 0.035 * g, 0.2)
def murmur(t0, t1, g0, g1):
    n = S.smp(t1 - t0); x = np.arange(n) / S.SR
    y = S.bp(S.noise(n), 220, 1100) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.31 * x + 1) * np.sin(2 * np.pi * 0.83 * x)) + S.bp(S.noise(n), 90, 300) * 0.5
    env = np.linspace(g0, g1, n) * np.clip(x / 1.5, 0, 1) * np.clip((t1 - t0 - x) / 1.5, 0, 1)
    fx.add(t0, S.autopan(y * env, -0.4, 0.4), 0.11)
def creak(t0, dur, g=1.0):
    n = S.smp(dur); x = np.arange(n) / S.SR; f = 170 + 120 * x / dur + 12 * np.sin(2 * np.pi * 7 * x)
    y = S.bp(S.saw(f, n) * (np.sin(2 * np.pi * 23 * x) > -0.3), 300, 1800)
    fx.add(t0, y * np.sin(np.pi * x / dur) ** 0.7, 0.03 * g, 0.2)


def crickets(t0, t1, g=1.0):
    n = S.smp(t1 - t0); x = np.arange(n) / S.SR
    y = np.zeros(n)
    for f, rate, ph in ((4300, 3.1, 0.0), (4750, 2.3, 1.7), (5200, 3.7, 0.6)):
        y += np.sin(2 * np.pi * f * x) * (np.sin(2 * np.pi * 38 * x) > 0.2) * np.clip(np.sin(2 * np.pi * rate / 4 * x + ph), 0, 1) ** 3
    env = np.clip(x / 2, 0, 1) * np.clip((t1 - t0 - x) / 2, 0, 1)
    fx.add(t0, S.autopan(y * env, -0.6, 0.6), 0.013 * g)
    w = S.bp(S.noise(n), 90, 420) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.07 * x)) * env      # wind; the first pass was all rumble
    fx.add(t0, w, 0.022 * g, 0.0)
def growl(t, dur=1.4, g=1.0, pan=0.0):
    n = S.smp(dur); x = np.arange(n) / S.SR
    f = 58 - 12 * x / dur + 3 * np.sin(2 * np.pi * 5 * x)
    y = S.saw(f, n) * (0.55 + 0.45 * np.sin(2 * np.pi * 24 * x)) + 0.4 * S.bp(S.noise(n), 150, 700)
    y = S.bp(y, 70, 900) + 0.5 * S.bp(y, 300, 620)
    fx.add(t, S.saturate(y * np.sin(np.pi * x / dur) ** 0.7, 1.6), 0.10 * g, pan)
def shot(t, g=1.0, pan=0.0):
    n = S.smp(1.2); x = np.arange(n) / S.SR
    y = S.noise(n) * np.exp(-x / 0.035) + S.lp(S.noise(n), 500) * np.exp(-x / 0.25) * 0.5 + np.sin(2 * np.pi * 70 * x * (1 + np.exp(-x / 0.02))) * np.exp(-x / 0.1)
    fx.add(t, S.lp(y, 5200), 0.20 * g, pan)
def drum(t, g=1.0, m=41): low.add(t, inst(TIMP, m, 1.0, 62), 0.7 * g)
def heart(t0, t1, gap0=1.0, gap1=1.0, g0=0.5, g1=0.5):
    t = t0
    while t < t1:
        p = (t - t0) / max(1e-6, t1 - t0); g = g0 + (g1 - g0) * p
        drum(t, g, 40); drum(t + 0.22, g * 0.7, 40); t += gap0 + (gap1 - gap0) * p
def chuff(t0, t1, rate0=2.0, rate1=2.0, g=1.0):
    t = t0
    while t < t1:
        p = (t - t0) / max(1e-6, t1 - t0); n = S.smp(0.16); x = np.arange(n) / S.SR
        fx.add(t, S.bp(S.noise(n), 300, 2600) * np.exp(-x / 0.05), 0.09 * g * np.sin(np.pi * min(1, max(0.05, p))) ** 0.5, -0.3 + 0.6 * p); t += 1 / (rate0 + (rate1 - rate0) * p)
def whistle(t, dur=1.2, g=1.0):
    n = S.smp(dur); x = np.arange(n) / S.SR; v = 1 + 0.004 * np.sin(2 * np.pi * 6 * x)
    y = (np.sin(2 * np.pi * 740 * v * x) + 0.8 * np.sin(2 * np.pi * 932 * v * x) + 0.3 * S.bp(S.noise(n), 700, 2500)) * np.clip(x / 0.08, 0, 1) * np.clip((dur - x) / 0.25, 0, 1)
    fx.add(t, y, 0.03 * g, -0.2)
def crackle(t0, t1, g=1.0):
    for t in np.sort(rng.uniform(t0, t1, int((t1 - t0) * 5))): n = S.smp(0.03); x = np.arange(n) / S.SR; fx.add(t, S.hp(S.noise(n), 2500) * np.exp(-x / 0.004), 0.03 * g * rng.uniform(0.3, 1), rng.uniform(-0.3, 0.5))
def drone(t0, t1, notes=(28, 40), vel=42, g=0.6): strings(t0, [m + 12 if m < 36 else m for m in notes], t1 - t0, vel, g * 0.8, swell=3)   # an octave up: E1 made the bed bottom-heavy
def motif(t, notes, step=1.0, vel=74, g=1.0, fn=None):
    for k, m in enumerate(notes): (fn or kal)(t + k * step, m, vel - 3 * (k % 2), g)


Am, F, C, G, Dm, E, A, D = (45, 52, 57, 60), (41, 48, 53, 57), (48, 55, 60, 64), (43, 50, 55, 59), (50, 57, 62, 65), (40, 47, 52, 56), (45, 52, 57, 61), (50, 57, 62, 66)
CEL, TUB = 8, 14
def cel(t, m, vel=64, g=1.0, pan=0.2): mus.add(t, inst(CEL, m, 1.6, vel), g * 1.5, pan)
def toll(t, m=57, g=1.0): mus.add(t, inst(TUB, m, 4.0, 70), g * 1.0, -0.2)
def wind(t0, t1, g=1.0):
    n = S.smp(t1 - t0); x = np.arange(n) / S.SR
    w = S.bp(S.noise(n), 160, 900) * (0.55 + 0.45 * np.sin(2 * np.pi * 0.07 * x + 1) * np.sin(2 * np.pi * 0.13 * x)) + 0.22 * S.bp(S.noise(n), 700, 2200) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.19 * x)) ** 2
    fx.add(t0, S.autopan(w * np.clip(x / 2, 0, 1) * np.clip((t1 - t0 - x) / 2, 0, 1), -0.5, 0.5), 0.032 * g)
def paws(t0, t1, g=1.0, rate=5.0):
    for t in np.arange(t0, t1, 1 / rate):
        n = S.smp(0.07); x = np.arange(n) / S.SR
        fx.add(t + rng.uniform(0, 0.02), S.bp(S.noise(n), 500, 2400) * np.exp(-x / 0.015), 0.035 * g * rng.uniform(0.6, 1), rng.uniform(-0.4, 0.4))
def bells(t0, t1, g=1.0, step=0.5):
    for k, t in enumerate(np.arange(grid(t0), t1, step)): clink(t, 101 + (0, 3, 0, 5)[k % 4], 0.55 * g, 0.3)
def run(t0, t1, g=1.0):
    e = lambda t: g * min(1, (t - t0) / 1.5, (t1 - t) / 1.5)
    for t in np.arange(t0, t1 - 0.4, 2.0): paws(t, min(t + 2.0, t1), e(t + 1) * 1.0); bells(t, min(t + 2.0, t1), e(t + 1))
def crack(t, g=1.0):
    n = S.smp(1.6); x = np.arange(n) / S.SR
    y = S.noise(n) * np.exp(-x / 0.03) + S.lp(S.noise(n), 600) * np.exp(-x / 0.4) * 0.8 + np.sin(2 * np.pi * 80 * x * (1 + np.exp(-x / 0.05))) * np.exp(-x / 0.25)
    fx.add(t, S.lp(y, 4200), 0.16 * g, rng.uniform(-0.5, 0.5))
def keys(t0, t1, n, g=1.0):
    for t in np.linspace(t0, t1, n): tick(t + rng.uniform(0, 0.03), rng.random() < 0.5, g)
def lay(t0, t1, chords, fn):
    for k, t in enumerate(bars(t0, t1)): fn(k, t, chords[k % len(chords)])

# ================================================================ 1. the drift
q0 = lambda p: q(0, p)
wind(0.2, V[1] + 1, 2.2); drone(0.5, V[1], (33, 45), 44, 0.8)
motif(SC[0]['start'] - 1.5, [69, 76, 72], 1.2, 66, 0.9, fn=lambda t, m, v, g: piano(t, m, 4, v, g))
heart(q0('he has pulled'), q0('and if he cant'), 1.0, 0.7, 0.4, 0.8); scratch(q0('he has pulled') + 1.5, 1.2, 1.0); scratch(q0('somewhere in that') + 0.5, 1.4, 1.0)
for k, m in enumerate((57, 55, 53, 52)): cello(q0('it has come') + k * 1.3, m - 12, 1.4, 62, 0.9)
qO = q0('children are'); low.add(qO - 0.05, inst(TIMP, 45, 3, 98), 1.4); strings(qO, Am, V[1] - qO + 1.2, 74, 0.9, swell=0.6); motif(qO + 0.5, [81, 76, 72, 69], 0.5, 76, 1.0, fn=lambda t, m, v, g: piano(t, m, 4, v, g))

# ================================================================ 2. Nome
q1 = lambda p: q(1, p)
wind(V[1], V[2] + 1, 0.8)
lay(V[1] + 0.8, q1('and in the winter') - 0.5, (Am, F, C, G), lambda k, t, ch: (cello(t, ch[0] - 12, 3.8, 56, 0.8), [cel(t + e * 0.5, ch[(e * 3 + k) % 4] + 24, 60, 0.8) for e in range(8) if e % 4 != 3]))
for p in ('no road', 'no railroad', 'no ships'): thud(q1(p) + 0.25, 0.8, 90); swish(q1(p), 1.0, 0.3)
qW = q1('and in the winter'); strings(qW, (45, 52, 57), V[2] - qW + 0.4, 50, 0.8, swell=1.5)
for k, m in enumerate((57, 60, 64, 62, 60, 57)): piano(q1('his name was') + k * 1.1, m, 4, 58, 0.85)

# ================================================================ 3. the outbreak
q2 = lambda p: q(2, p)
drone(V[2] + 0.2, q2('welch knew'), (33, 45), 44, 0.8); crackle(V[2] + 0.5, q2('welch knew'), 0.4)
for k, m in enumerate((69, 68, 69, 64)): piano(SC[2]['start'] + 0.4 + k * 1.2, m, 4, 54, 0.8)
piano(q2('boy died') + 0.5, 45, 6, 68, 1.0); piano(q2('boy died') + 0.5, 33, 6, 60, 0.9); swish(q2('boy died') + 0.4, 0.5, 0.5)
piano(q2('7yearold') + 1.0, 44, 6, 68, 1.0); piano(q2('7yearold') + 1.0, 32, 6, 60, 0.9); swish(q2('7yearold') + 0.9, 0.5, 0.5)
qD = q2('diphtheria'); low.add(qD - 0.05, inst(TIMP, 45, 3, 100), 1.4); strings(qD, (45, 51, 57, 60), q2('there was a cure') - qD, 62, 0.9, prog=TREM, swell=0.5); toll(qD + 1.5, 45, 0.9); toll(qD + 4.5, 45, 0.7); wind(qD - 0.5, q2('there was a cure'), 0.8)
qC = q2('there was a cure')
for k, m in enumerate((69, 72, 76, 81)): cel(qC + 0.3 + k * 0.25, m, 70, 1.0)
strings(qC, (45, 52, 57, 60, 64), q2('had expired') - qC, 56, 0.8, swell=1.0)
thud(q2('had expired') + 0.2, 1.3, 70); piano(q2('had expired') + 0.2, 33, 5, 78, 1.1)
qT = q2('an epidemic is almost'); keys(qT - 0.2, SC[2]['end'] - 0.4, 90, 0.9); cello(q2('so he sent'), 33, V[3] - q2('so he sent'), 62, 0.9); clack(SC[2]['end'] - 0.3, 1.2, 800)

# ================================================================ 4. the map
q3 = lambda p: q(3, p)
for k, t in enumerate(np.arange(grid(V[3] + 0.6), q3('there were three') - 0.6, 0.5)):
    ch = (Am, C, F, G)[int(k // 8) % 4]; pizz(t, ch[0] - 12 + (0, 7)[k % 2], 68, 0.8)
    if k % 2 == 0: piano(t, ch[(k // 2) % 4] + 12, 2, 54, 0.65)
clink(q3('they found') + 0.1, 96, 1.6); chuff(q3('a train could'), q3('and there the tracks'), 3.0, 5.0, 0.9); whistle(q3('a train could') + 0.3, 1.0, 0.8); thud(q3('and there the tracks') + 0.5, 1.2, 70)
low.add(q3('674 miles'), inst(TIMP, 45, 3, 92), 1.2); strings(q3('from the end'), Am, q3('there were three') - q3('from the end'), 56, 0.8, swell=1.5)
qP = q3('there were three')
for k in range(3): thud(qP + 0.3 + k * 0.25, 0.6, 120)
lay(qP, q3('that left') - 0.4, (Dm, E), lambda k, t, ch: (cello(t, ch[0] - 12, 3.8, 60, 0.9), piano(t + 1, ch[2], 4, 50, 0.7), piano(t + 2.5, ch[3], 4, 48, 0.7)))
for k in range(4): clack(q3('were in pieces') + k * 0.16, 0.8, 300 + 60 * k)
qL = q3('that left'); paws(qL + 0.2, q3('by dog') + 0.2, 1.4); low.add(q3('by dog') + 0.1, inst(TIMP, 45, 3, 96), 1.3); strings(q3('by dog') + 0.1, (45, 52, 57, 60, 64), V[4] - q3('by dog') + 0.4, 66, 0.9, swell=0.5)

# ================================================================ 5. the relay
q4 = lambda p: q(4, p)
for k, t in enumerate(np.arange(grid(V[4] + 0.6), q4('the package was') - 0.8, 0.5)):
    ch = (Am, F, C, G)[int(k // 8) % 4]; lvl = min(1.0, 0.5 + k / 50); pizz(t, ch[0] - 12 + (0, 7)[k % 2], 70, 0.8 * lvl)
    if k % 2 == 0: cel(t, ch[(k // 2) % 4] + 24, 62, 0.8 * lvl)
    if k % 8 == 0: strings(t, ch, 4.3, 44 + int(20 * lvl), 0.6 * lvl, swell=0.8)
keys(q4('they sent twenty'), q4('twenty drivers') + 2.4, 20, 1.2)
qK = q4('the package was'); drone(qK - 0.4, q4('at every stop'), (33, 45, 52), 46, 0.8); clink(q4('packed with glass'), 100, 1.4); clink(q4('packed with glass') + 0.15, 104, 1.1); clink(q4('packed with glass') + 0.3, 108, 0.9)
qS = q4('at every stop'); wind(qS - 0.5, V[5] + 1, 1.0); crackle(qS, q4('many of them'), 1.2); lay(qS, q4('many of them') - 0.4, (F, C), lambda k, t, ch: (strings(t, ch, 4.3, 50, 0.7, swell=1.0), harp(t + 1, ch[2] + 12, 60, 0.8), harp(t + 2, ch[3] + 12, 58, 0.7)))
qM = q4('many of them'); run(qM - 0.3, V[5], 1.0); lay(qM, V[5] - 0.3, (Am, G), lambda k, t, ch: (cello(t, ch[0] - 12, 3.8, 60, 0.9), strings(t, ch, 4.3, 50, 0.7, swell=1.0)))

# ================================================================ 6. the first driver
q5 = lambda p: q(5, p)
chuff(V[5], SC[5]['start'] + 3.2, 4.5, 1.2, 1.0); whistle(V[5] + 0.6, 1.3, 0.9); wind(V[5], V[6] + 1, 1.1)
strings(V[5] + 0.3, (45, 52, 57), q5('he tied') - V[5], 50, 0.8, swell=1.5)
qO5 = q5('and went out'); run(qO5 - 0.3, q5('when he came in') - 0.4, 1.0); heart(q5('it was fifty'), q5('he ran beside'), 1.0, 0.8, 0.4, 0.6)
for k, m in enumerate((69, 67, 65, 64)): piano(q5('it was fifty') + 0.2 + k * 0.22, m, 3, 60, 0.8)
for k, m in enumerate((64, 62, 60, 57, 52, 45)): piano(q5('it dropped to') + 0.2 + k * 0.2, m, 3, 62, 0.85)
strings(q5('it was fifty'), (45, 51, 57), q5('when he came in') - q5('it was fifty'), 50, 0.8, prog=TREM, swell=1.5)
qI = q5('when he came in'); crackle(qI, V[6], 1.2); lay(qI - 0.3, V[6] - 0.3, (Dm, Am, E), lambda k, t, ch: (cello(t, ch[0] - 12, 3.8, 60, 0.9), piano(t + 1, ch[2], 4, 50, 0.7), piano(t + 2.5, ch[3], 4, 48, 0.7)))
fx.add(q5('they had to pour'), S.whoosh(1.6, 1800, 6500, 0.9), 0.045, -0.3)

# ================================================================ 7. hand to hand
q6 = lambda p: q(6, p)
qE = q6('one driver')
for k, t in enumerate(np.arange(grid(V[6] + 0.4), qE - 0.6, 0.5)):
    ch = (Am, C, F, G)[int(k // 8) % 4]; pizz(t, ch[0] - 12 + (0, 7)[k % 2], 70, 0.8)
    if k % 2 == 0: cel(t, ch[(k // 2) % 4] + 24, 62, 0.8)
paws(V[6] + 0.3, qE - 0.6, 0.6)
for p, m in (('thirty miles', 81), ('twenty eight', 84), ('forty', 88)): harp(q6(p), m, 72, 1.0)
wind(qE - 0.5, V[7] + 1, 1.2); paws(qE, q6('in nome the town') - 0.5, 0.8, 3.0)
for k, m in enumerate((57, 55, 53, 52, 50, 52)): cello(qE + 0.3 + k * 1.35, m - 12, 1.4, 64, 1.0)
qN = q6('in nome the town'); toll(qN - 0.2, 45, 1.0); toll(qN + 3.0, 45, 0.8); toll(qN + 6.0, 45, 0.7); strings(qN, (45, 52, 57, 60), V[7] - qN + 0.4, 52, 0.8, swell=1.5)

# ================================================================ 8. Seppala and Togo
q7 = lambda p: q(7, p)
qPup, qLf, qSer, qAr = q7('as a pup'), q7('they left nome'), q7('the serum the serum'), q7('around the bay')
lay(V[7] + 0.5, qPup - 0.5, (F, C, Dm, C), lambda k, t, ch: (strings(t, ch, 4.3, 54, 0.8, swell=1.0), harp(t, ch[1] + 12, 62, 0.8), harp(t + 1, ch[2] + 12, 58, 0.8), harp(t + 2, ch[3] + 12, 60, 0.8)))
for k, m in enumerate((77, 81, 84)): cel(q7('his lead dog') + 1.0 + k * 0.2, m, 70, 1.0)
for k, t in enumerate(np.arange(grid(qPup), q7('seppala kept') - 0.3, 0.5)): pizz(t, (48, 55, 53, 55)[k % 4], 72, 0.8); (cel(t + 0.25, (72, 76, 79, 76)[k % 4] + 12, 60, 0.7) if k % 2 else None)
qJ = q7('togo jumped')
for k in range(7): clink(qJ + 0.1 + k * 0.05, 96 + rng.integers(0, 14), 1.3, rng.uniform(-0.4, 0.4))
fx.add(qJ + 0.08, S.hp(S.noise(S.smp(0.4)), 3000) * np.exp(-np.arange(S.smp(0.4)) / S.SR / 0.08), 0.06, 0.0); paws(qJ + 0.8, q7('seppala kept') - 0.2, 1.4, 7.0)
piano(q7('seppala kept') + 0.3, 60, 4, 60, 0.9); piano(q7('seppala kept') + 0.7, 64, 4, 56, 0.8)
for k, t in enumerate(np.arange(grid(qLf), qSer - 0.6, 0.5)):
    ch = (Am, C, F, G)[int(k // 8) % 4]; pizz(t, ch[0] - 12 + (0, 7)[k % 2], 70, 0.8)
    if k % 2 == 0: piano(t, ch[(k // 2) % 4] + 12, 2, 54, 0.65)
run(qLf, qSer - 0.5, 0.6)
wind(qSer - 0.6, qAr, 2.4); run(qSer - 0.4, qSer + 1.6, 1.0); low.add(qSer + 0.3, inst(TIMP, 45, 3, 90), 1.2); strings(qSer, (45, 52, 57, 60), qAr - qSer, 60, 0.9, prog=TREM, swell=0.6)
heart(qAr, q7('he went across'), 1.0, 0.7, 0.45, 0.85); strings(qAr, (45, 51, 57), V[8] - qAr, 48, 0.8, prog=TREM, swell=2); swish(qAr + 0.1, 1.2, 0.6); swish(q7('or straight across'), 1.2, 0.4)
crack(q7('already cracking') - 0.2, 0.9); crack(q7('already cracking') + 0.5, 0.6)
qG = q7('he went across'); low.add(qG + 0.1, inst(TIMP, 45, 4, 104), 1.5); cello(qG + 0.1, 33, V[8] - qG, 70, 1.0)

# ================================================================ 9. the ice
q8 = lambda p: q(8, p)
qSl, qBh, qTh, qBy = q8('they slept'), q8('behind them'), q8('then togo led'), q8('by the time')
wind(V[8], qSl + 0.5, 2.6); run(V[8], qSl - 0.5, 1.0); heart(V[8] + 1, q8('and brought them in'), 0.8, 0.6, 0.5, 0.8)
lay(V[8] + 0.3, q8('and the old dog'), (Am, F), lambda k, t, ch: strings(t, ch, 4.3, 56, 0.8, prog=TREM, swell=0.8))
for t in (q8('seppala could not') + 0.4, q8('so he left it') + 1.0): crack(t, 0.5)
qOld = q8('and the old dog'); strings(qOld, (45, 52, 57, 60, 64), qSl - qOld, 60, 0.9, swell=2.0)
for k, m in enumerate((69, 72, 76, 81)): harp(q8('and brought them in') + k * 0.25, m, 66, 0.9)
crackle(q8('and brought them in'), qBh, 1.0)
wind(qBh - 0.5, qBy, 1.6); crack(q8('broke up') - 0.3, 1.5); crack(q8('broke up') + 0.3, 1.1); crack(q8('broke up') + 1.0, 0.9); crack(q8('broke up') + 1.9, 0.6)
strings(qBh, (45, 51, 57, 60), qTh - qBh, 56, 0.9, prog=TREM, swell=1.0); cello(qBh, 33, qTh - qBh, 64, 0.9)
run(qTh, qBy - 0.5, 0.8)
for k, ch in enumerate((Am, C, Dm, E)): strings(qTh + k * 1.0, ch, 1.4, 54 + 5 * k, 0.8, swell=0.4)
for k, t in enumerate(np.arange(grid(qBy), q8('261 miles') - 0.3, 0.25)): harp(t, 57 + (0, 3, 7, 12, 15, 19, 24)[k % 7], 60, 0.7)
q261 = q8('261 miles'); low.add(q261, inst(TIMP, 45, 4, 100), 1.4); strings(q261, (45, 52, 57, 61, 64), V[9] - q261 + 0.3, 68, 1.0, swell=0.5); harp(q261, 81, 76, 1.0); harp(q261 + 0.15, 85, 72, 0.9)

# ================================================================ 10. the last driver
q9 = lambda p: q(9, p)
qNm, qLf9, qGu, qGone, qTk, qMt = q9('his name was'), q9('he left at ten'), q9('then a gust'), q9('was gone'), q9('he took off'), q9('on metal')
wind(V[9], V[10] + 1, 2.8); drone(V[9] + 0.3, qNm, (33, 45), 48, 0.8)
keys(q9('the doctor sent word'), q9('the message never'), 26, 1.0); clack(q9('the message never') + 0.3, 2.0, 500); fx.add(q9('the message never') + 0.3, S.whoosh(1.2, 600, 3000, 0.9), 0.07, 0.0); piano(q9('the message never') + 0.5, 33, 5, 74, 1.0)
lay(qNm, qLf9 - 0.3, (Am, E), lambda k, t, ch: (cello(t, ch[0] - 12, 3.8, 62, 0.9), piano(t + 1, ch[2], 4, 52, 0.7), piano(t + 2.5, ch[3], 4, 50, 0.7)))
run(qLf9, qGu, 1.0); heart(qLf9 + 1, qGu, 0.8, 0.55, 0.5, 0.9)
lay(qLf9, qGu - 0.3, (Am, F, Dm), lambda k, t, ch: strings(t, ch, 4.3, 54 + 6 * k, 0.8 + 0.05 * k, prog=TREM, swell=0.8))
fx.add(qGu + 0.1, S.whoosh(1.4, 400, 4200, 0.9), 0.11, 0.0); thud(q9('and threw it') + 0.1, 1.6, 55); clack(q9('and threw it') + 0.15, 1.4, 260); low.add(q9('and threw it') + 0.1, inst(TIMP, 45, 3, 104), 1.4)
piano(qGone, 33, 6, 78, 1.1); piano(qGone, 45, 6, 68, 0.9); cello(qGone, 33, qMt - qGone, 60, 0.8)
heart(qTk, qMt, 0.7, 0.5, 0.6, 0.95)
for t in np.arange(qTk + 0.9, qMt - 0.3, 0.8): scratch(t, 0.6, 1.3)
clink(qMt, 88, 2.2); clink(qMt + 0.1, 100, 1.4); strings(qMt + 0.1, (45, 52, 57, 61, 64), V[10] - qMt + 0.5, 66, 1.0, swell=0.8)

# ================================================================ 11. Front Street
q10 = lambda p: q(10, p)
q530, qUn, q674, q5d = q10('at 530'), q10('the doctor unwrapped'), q10('six hundred and seventy'), q10('in 5')
wind(V[10], qUn, 1.6); run(V[10], q10('balto pulled') + 2.2, 1.0)
lay(V[10] + 0.4, q530 - 0.4, (Am, F, G), lambda k, t, ch: (cello(t, ch[0] - 12, 3.8, 62, 0.9), strings(t, ch, 4.3, 52, 0.8, swell=1.0)))
lay(q530, qUn - 0.3, (F, C, G, Am), lambda k, t, ch: (strings(t, ch, 4.3, 56 + 4 * k, 0.85, swell=1.0), harp(t, ch[1] + 12, 62, 0.8), harp(t + 1, ch[2] + 12, 60, 0.8), harp(t + 2, ch[3] + 12, 62, 0.8), harp(t + 3, ch[2] + 12, 58, 0.8)))
toll(q10('balto pulled') + 1.5, 57, 0.9)
for k in range(11): clink(qUn + 0.6 + k * 0.12, 96 + k, 1.2, -0.5 + k * 0.1)
strings(qUn, (45, 52, 57, 61), q674 - qUn, 54, 0.8, swell=1.5)
low.add(q674, inst(TIMP, 45, 4, 102), 1.5); strings(q674, (33, 45, 52, 57, 61, 64, 69), V[11] - q674 + 0.6, 74, 1.1, swell=0.6)
for k, m in enumerate((69, 73, 76, 81, 85, 88)): harp(q674 + 0.3 + k * 0.2, m, 70, 0.9)
low.add(q5d, inst(TIMP, 40, 3, 92), 1.2); piano(q5d, 57, 5, 70, 1.0); piano(q5d, 61, 5, 66, 0.9); piano(q5d, 64, 5, 66, 0.9)

# ================================================================ 12. after
q11 = lambda p: q(11, p)
lay(V[11] + 0.6, q11('every driver got') - 0.4, (A, D, A, E), lambda k, t, ch: (cello(t, ch[0] - 12, 3.8, 60, 0.9), arp(t, ch, 54, 0.85)))
piano(q11('the doctor believed') + 0.4, 42, 5, 62, 0.9)
qEv = q11('every driver got')
for i in range(20): clink(qEv + 0.4 + i * 0.07, 98 + (i % 5) * 2, 0.9, -0.5 + i * 0.05)
lay(qEv, q11('a second shipment') - 0.3, (D, A), lambda k, t, ch: (strings(t, ch, 4.3, 56, 0.8, swell=1.0), harp(t + 1, ch[2] + 12, 60, 0.8)))
run(q11('a second shipment') - 0.3, V[12], 0.9); lay(q11('a second shipment'), V[12] - 0.3, (A, E), lambda k, t, ch: (cello(t, ch[0] - 12, 3.8, 60, 0.9), arp(t, ch, 54, 0.8)))

# ================================================================ 13. Balto and Togo
q12 = lambda p: q(12, p)
qBf, qTn, qCh, qTg, qRt = q12('before the year'), q12('then the country'), q12('the children of cleveland'), q12('and togo'), q12('he retired')
thud(V[12] + 0.8, 0.9, 150); swish(V[12] + 0.3, 1.2, 0.5)
for k, t in enumerate(np.arange(grid(V[12] + 0.5), qBf - 0.5, 0.5)): pizz(t, (45, 52, 50, 52)[k % 4], 72, 0.8); (cel(t, (69, 73, 76, 73)[k % 4] + 12, 62, 0.8) if k % 2 == 0 else None)
strings(qBf, (45, 52, 57, 61, 64), qTn - qBf, 64, 1.0, swell=1.5)
for k, m in enumerate((69, 73, 76, 81)): harp(q12('a bronze statue') + k * 0.22, m, 68, 0.9)
for k, m in enumerate((57, 56, 52, 50, 48, 45)): cello(qTn + 0.2 + k * 1.3, m - 12, 1.4, 62, 1.0)
drone(qTn, qCh, (33, 45), 44, 0.7)
for k in range(3): clink(q12('he ended up') + 1.6 + k * 0.5, 80, 0.9, 0.3)
for k, t in enumerate(np.arange(grid(qCh), qTg - 0.5, 0.5)):
    ch = (C, G, F, G)[int(k // 8) % 4]; pizz(t, ch[0] - 12 + (0, 7)[k % 2], 70, 0.8)
    if k % 2 == 0: cel(t, ch[(k // 2) % 4] + 24, 64, 0.85)
for i in range(18): clink(q12('raised the money') - 0.3 + i * 0.12, 100 + (i % 6), 1.0, rng.uniform(-0.4, 0.4))
paws(q12('and brought him'), qTg - 0.3, 1.0, 4.0)
piano(qTg + 0.1, 57, 4, 60, 0.9); piano(qTg + 0.6, 60, 4, 56, 0.8)
for k, t in enumerate(np.arange(q12('togo ran five') - 0.2, q12('togo ran five') + 1.2, 0.2)): harp(t, 57 + k * 3, 62, 0.8)
low.add(q12('togo ran five') + 1.2, inst(TIMP, 45, 3, 88), 1.1)
crackle(qRt, V[13], 1.3); lay(qRt - 0.3, V[13] - 0.3, (F, C, Dm, E), lambda k, t, ch: (cello(t, ch[0] - 12, 3.8, 56, 0.9), piano(t, ch[1], 4, 54, 0.8), piano(t + 1, ch[2], 4, 50, 0.75), piano(t + 2, ch[3], 4, 52, 0.75), piano(t + 3, ch[2], 4, 48, 0.7)))

# ================================================================ 14. the three words
q13 = lambda p: q(13, p)
qSt, qSub, qAn, qBat, qCol = q13('and the statue'), q13('subscribe'), q13('animal facts'), q13('historys greatest'), q13('worlds craziest')
lay(V[13] + 0.4, qSt - 0.4, (Am, F, C), lambda k, t, ch: (cello(t, ch[0] - 12, 3.8, 58, 0.9), piano(t, ch[1], 4, 54, 0.8), piano(t + 1.5, ch[2], 4, 50, 0.75), piano(t + 3, ch[3], 4, 50, 0.75)))
strings(qSt - 0.2, (33, 45, 52, 57, 61, 64), qSub - qSt + 0.4, 66, 1.0, swell=1.8)
for p, m in (('endurance', 69), ('fidelity', 73), ('intelligence', 76)): low.add(q13(p), inst(TIMP, 45, 3, 84), 1.0); harp(q13(p), m, 74, 1.0); harp(q13(p) + 0.12, m + 12, 68, 0.9); piano(q13(p), m - 12, 5, 62, 0.9)
e0 = qSub
low.add(e0, inst(TIMP, 45, 3, 92), 1.2); strings(e0, (33, 45, 52, 57, 61, 64), DUR - e0 - 0.5, 70, 1.0, swell=0.8)
for k, (t, m) in enumerate(zip(np.arange(e0 + 0.5, DUR - 5.5, 1.0), [69, 76, 74, 73, 69, 76, 78, 76, 73, 74, 76, 81] * 3)): cel(t, m + 12, 70, 0.9); piano(t, m, 3.5, 52, 0.6)
bells(e0 + 0.5, DUR - 6, 0.8)
for at, m in ((qAn, 81), (qBat, 85), (qCol, 88)): harp(at, m, 76, 1.0); harp(at + 0.12, m + 7, 70, 0.8)
tend = DUR - 5.2
for k, m in enumerate((33, 45, 52, 57, 61, 64, 69)): piano(tend + k * 0.16, m, 6, 68, 1.0)
low.add(tend, inst(TIMP, 45, 4, 80), 1.0)

# ---------------------------------------------------------------- mix
# an eight-minute film is too long to hold every bus and its copies at once: finish one bed, free it, then the other
import gc
_cache.clear()
DN = S.smp(DUR); tt_ = np.arange(DN) / S.SR; fade = np.clip(tt_ / 0.5, 0, 1) * np.clip((DUR - tt_) / 3.0, 0, 1)
f = fx.out(True).astype(np.float32); del fx; gc.collect()
lo_ = low.out(True)[:, :mus.x.shape[1]]
m = mus.out(True) * 1.1 + lo_ * 0.85
wet = S.reverb(mus.out(True) * 0.6 + lo_ * 0.25, S.hall(4.0, 1.3, 0.03, 220, 6500), 0.5)
del mus, low, lo_; gc.collect()
m = (m + wet)[:, :DN]; del wet; gc.collect()
m = S.eq(m, [('lowshelf', 110, -5.0, 0.7), ('peak', 280, -5.5, 0.9), ('peak', 520, -3.0, 1.0), ('peak', 1500, 2.0, 0.8), ('peak', 3000, 5.0, 0.8), ('highshelf', 4500, 10.0, 0.7)])
S.write('music.wav', S.master(m * fade, lufs=-20.0, fade=0, ceiling=0.8)); del m; gc.collect()
f = f.astype(np.float64); f = (f + S.reverb(f * 0.5, S.plate(1.8, 0.5), 0.45))[:, :DN]
f = S.eq(S.hp(f, 62), [('lowshelf', 120, -2.0, 0.7), ('peak', 3200, -4.0, 0.8), ('highshelf', 6000, -2.0, 0.7)])
S.write('fx.wav', S.limiter(f * fade * 2.2, 0.7))
print('music.wav, fx.wav', round(DUR, 2), 's')
