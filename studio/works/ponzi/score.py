#!/usr/bin/env python3
"""score.py: the music and sound for Ponzi, written against the narration's own timing.

Reads timing.json (from film_voice.py), writes music.wav and fx.wav.
G major stride piano while the money comes in, with a till bell and coins on every number; E minor, a clock and
plucked strings once the arithmetic starts; a gavel at the end of the fall; it closes in E major.
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

S.seed(1920)
rng = np.random.default_rng(1920)
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


Em, C, Am, B, G, D, E, A = (52, 59, 64, 67), (48, 55, 60, 64), (45, 52, 57, 60), (47, 54, 59, 63), (43, 50, 55, 59), (50, 57, 62, 66), (52, 59, 64, 68), (45, 52, 57, 61)
HORN, TRB = 60, 57
def horn(t, m, dur=2.0, vel=64, g=1.0): mus.add(t, inst(HORN, m, dur, vel), g * 1.1, -0.2)
def waves(t0, t1, g=1.0):
    n = S.smp(t1 - t0); x = np.arange(n) / S.SR
    w = S.bp(S.noise(n), 120, 900) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.11 * x + 1)) ** 2 + 0.35 * S.bp(S.noise(n), 900, 3000) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.11 * x + 2.2)) ** 6
    fx.add(t0, S.autopan(w * np.clip(x / 2, 0, 1) * np.clip((t1 - t0 - x) / 2, 0, 1), -0.4, 0.4), 0.03 * g)
def engines(t0, t1, g=1.0, f0=92, rise=0.0, pan=(-0.5, 0.5)):
    n = S.smp(t1 - t0); x = np.arange(n) / S.SR; f = f0 * (1 + rise * x / max(1e-6, t1 - t0)) * (1 + 0.006 * np.sin(2 * np.pi * 0.7 * x))
    y = S.saw(f, n) * 0.6 + S.saw(f * 1.5, n) * 0.3 + 0.3 * S.bp(S.noise(n), 200, 1200)
    y = S.lp(y * (0.8 + 0.2 * np.sin(2 * np.pi * f0 / 7 * x)), 900)
    fx.add(t0, S.autopan(y * np.clip(x / 1.2, 0, 1) * np.clip((t1 - t0 - x) / 1.2, 0, 1), *pan), 0.035 * g)
def dive(t, dur=2.3, g=1.0, pan=0.3):
    n = S.smp(dur); x = np.arange(n) / S.SR; f = 180 * (1 + 2.2 * (x / dur) ** 2)
    y = S.lp(S.saw(f, n) * 0.6 + S.saw(f * 2.01, n) * 0.3, 2600) * np.clip(x / 0.3, 0, 1) * np.clip((dur - x) / 0.15, 0, 1) * (0.3 + 0.7 * x / dur)
    fx.add(t, y, 0.05 * g, pan)
def boom(t, g=1.0, pan=0.0):
    n = S.smp(2.8); x = np.arange(n) / S.SR
    y = np.sin(2 * np.pi * 50 * x * (1 + 0.9 * np.exp(-x / 0.03))) * np.exp(-x / 0.4) + S.noise(n) * np.exp(-x / 0.06) * 0.8 + S.lp(S.noise(n), 500) * np.exp(-x / 0.8) * 0.8
    fx.add(t, S.lp(y, 3600), 0.30 * g, pan)
def pop(t, g=1.0):
    n = S.smp(0.5); x = np.arange(n) / S.SR
    fx.add(t, S.lp(S.noise(n), 1800) * np.exp(-x / 0.05) + np.sin(2 * np.pi * 90 * x) * np.exp(-x / 0.08) * 0.6, 0.07 * g, rng.uniform(-0.6, 0.6))
def flakf(t0, t1, per_s=1.6, g=1.0):
    for t in np.sort(rng.uniform(t0, t1, max(1, int((t1 - t0) * per_s)))): pop(t, g * rng.uniform(0.5, 1))
def splashf(t, g=1.0):
    n = S.smp(1.2); x = np.arange(n) / S.SR
    fx.add(t, S.bp(S.noise(n), 600, 4500) * np.clip(x / 0.05, 0, 1) * np.exp(-x / 0.35), 0.05 * g, rng.uniform(-0.5, 0.5))
def morse(t0, t1, g=1.0, f=720, wpm=0.085):
    t = t0
    while t < t1 - 0.2:
        d = wpm * (1 if rng.random() < 0.6 else 3); n = S.smp(d); x = np.arange(n) / S.SR
        fx.add(t, np.sin(2 * np.pi * f * x) * np.clip(x / 0.004, 0, 1) * np.clip((d - x) / 0.004, 0, 1), 0.022 * g, 0.3); t += d + wpm * (1 if rng.random() < 0.75 else 3)
def snare(t, g=1.0):
    n = S.smp(0.22); x = np.arange(n) / S.SR
    fx.add(t, S.bp(S.noise(n), 900, 6000) * np.exp(-x / 0.05) + np.sin(2 * np.pi * 190 * x) * np.exp(-x / 0.04) * 0.6, 0.05 * g, -0.15)
def march(t0, t1, g0=0.5, g1=0.5, step=0.5):
    for k, t in enumerate(np.arange(grid(t0), t1, step)):
        g = g0 + (g1 - g0) * (t - t0) / max(1e-6, t1 - t0); snare(t, g)
        if k % 4 == 3: snare(t + step * 0.5, g * 0.6); snare(t + step * 0.75, g * 0.6)
def keys(t0, t1, n, g=1.0):
    for t in np.linspace(t0, t1, n): tick(t + rng.uniform(0, 0.03), rng.random() < 0.5, g)
def lay(t0, t1, chords, fn):
    for k, t in enumerate(bars(t0, t1)): fn(k, t, chords[k % len(chords)])
def bed(k, t, ch, vel=54, g=0.8): cello(t, ch[0] - 12, 3.8, vel + 6, g + 0.1); strings(t, ch, 4.3, vel, g, swell=1.0)
def walk(t0, t1, chords, g=1.0, top=True):
    for k, t in enumerate(np.arange(grid(t0), t1 - 0.3, 0.5)):
        ch = chords[int(k // 8) % len(chords)]; pizz(t, ch[0] - 12 + (0, 7)[k % 2], 68, 0.8 * g)
        if top and k % 2 == 0: piano(t, ch[(k // 2) % 4] + 12, 2, 54, 0.65 * g)

# ---------------------------------------------------------------- Ponzi's own sounds
def ching(t, g=1.0, pan=0.2): clack(t, 0.5 * g, 900); clink(t + 0.07, 100, 1.7 * g, pan); clink(t + 0.15, 103, 1.3 * g, pan)
def coins(t0, t1, n, g=1.0):
    for t in np.sort(rng.uniform(t0, t1, n)): clink(t, int(rng.choice([93, 96, 98, 100, 103])), g * rng.uniform(0.6, 1.1), rng.uniform(-0.5, 0.5))
def gavel(t, g=1.0): clack(t, 1.3 * g, 260); thud(t, 0.5 * g, 110)
def stride(t0, t1, chords, g0=0.8, g1=None, mel=True):
    g1 = g0 if g1 is None else g1
    for k, t in enumerate(np.arange(grid(t0), t1 - 0.3, 0.5)):
        g = g0 + (g1 - g0) * (t - t0) / max(1e-6, t1 - t0); ch = chords[int(k // 8) % len(chords)]
        if k % 2 == 0: piano(t, ch[0] - 12 + (0, 7)[(k // 2) % 2], 1.5, 62, 0.8 * g, -0.2)
        else:
            for m in ch[1:]: piano(t, m, 1.0, 50, 0.42 * g, 0.15)
        if mel and k % 8 in (0, 3, 4, 6): piano(t + (0.25 if k % 8 == 3 else 0), ch[(k * 3 + int(k // 8)) % 4] + 24, 1.5, 60, 0.6 * g, 0.25)
def hit(t, vel=96, g=1.3, m=40): low.add(t - 0.05, inst(TIMP, m, 3, vel), g)
RISE = (G, C, D, G); RISE2 = (G, Em, C, D)

# ================================================================ 1. the line
q0 = lambda p: q(0, p)
qNot, qWk = q0('he has not made'), q0('and in three weeks')
murmur(0.3, V[1], 0.5, 1.0); stride(1.0, qNot - 0.4, RISE, 0.55, 0.8); coins(q0('every one of them'), qNot - 0.5, 14, 0.9)
for p in ('clerks', 'maids', 'shopkeepers', 'policemen'): pizz(q0(p), 43, 70, 0.7)
ching(q0('a quarter of a million') + 0.4, 1.2)
piano(qNot + 0.2, 40, 5, 66, 0.9); drone(qNot, qWk, (28, 40), 42, 0.7)
hit(qWk + 0.3); strings(qWk + 0.3, Em, V[1] - qWk + 1.0, 72, 1.0, swell=0.6); motif(qWk + 0.8, [76, 71, 67, 64], 0.5, 74, 1.0, fn=lambda t, m, v, g: piano(t, m, 4, v, g))

# ================================================================ 2. two dollars and fifty cents
q1 = lambda p: q(1, p)
qWk1, qWash = q1('he walked off'), q1('he washed dishes')
waves(V[1], qWash, 1.0); whistle(V[1] + 0.8, 1.6, 0.8)
lay(V[1] + 0.5, qWash - 0.4, (Em, C, G, D), lambda k, t, ch: (cello(t, ch[0] - 12, 3.8, 58, 0.9), arp(t, ch, 52, 0.85)))
coins(q1('he gambled away'), q1('he gambled away') + 1.8, 7, 0.9); creak(qWk1, 1.2, 0.9)
clink(q1('250'), 96, 1.5); clink(q1('250') + 0.8, 100, 1.3)
for k, m in enumerate((64, 67, 71, 76, 79, 83)): harp(q1('a million dollars in hopes') + k * 0.2, m, 68, 0.9)
walk(qWash, V[2] - 0.5, (Em, Am, B, Em), 0.9); clink(qWash + 0.5, 91, 1.0); clink(q1('he waited tables') + 0.5, 94, 1.0)
thud(q1('he got fired') + 0.4, 0.9, 90)

# ================================================================ 3. the bank in Montreal
q2 = lambda p: q(2, p)
qWo, qPay, qCol, qFg, qSeen = q2('ponzi worked out how'), q2('it was paying'), q2('the bank collapsed'), q2('forged a check'), q2('but he had seen')
walk(V[2] + 0.5, qWo - 0.4, (Am, Em, B, Em)); ching(q2('six percent') + 0.3, 1.1); ching(q2('double what') + 0.3, 0.9)
for k in range(5): tick(qWo + 0.2 + k * 0.5, k % 2 == 0, 1.0)
drone(qWo, qCol, (33, 45), 42, 0.7)
for k in range(6): clink(qPay + 0.3 + k * 0.45, 96 + (k % 2) * 4, 1.2, -0.5 + (k % 2))
hit(qCol + 0.2, 100, 1.4); thud(qCol + 0.2, 1.1, 60); strings(qCol + 0.2, (40, 47, 52, 58), qFg - qCol, 58, 0.9, prog=TREM, swell=0.5); coins(q2('the owner ran'), q2('the owner ran') + 1.5, 6, 0.8)
scratch(qFg + 0.2, 0.9, 1.4); gavel(q2('did three years') + 0.5, 1.0); thud(q2('then two more') + 0.5, 0.9, 80); clack(q2('then two more') + 0.5, 1.0, 300)
cello(qFg, 28, qSeen - qFg, 60, 0.9)
drone(qSeen - 0.3, V[3], (28, 40, 47), 44, 0.8); motif(qSeen + 0.4, [64, 67, 71], 1.0, 62, 0.9, fn=lambda t, m, v, g: piano(t, m, 4, v, g)); piano(q2('from the inside'), 40, 5, 66, 0.9)

# ================================================================ 4. the coupon
q3 = lambda p: q(3, p)
qLet, qNot3, qWar, qBuy, q400, qLeg = q3('then a letter came'), q3('ponzi noticed something'), q3('the war had wrecked'), q3('buy them there'), q3('on paper'), q3('and it was perfectly legal')
lay(V[3] + 0.5, qLet - 0.4, (Em, C, Am, B), lambda k, t, ch: (cello(t, ch[0] - 12, 3.8, 58, 0.9), piano(t + 1, ch[2], 4, 52, 0.7)))
swish(qLet + 0.3, 1.3, 0.5); harp(qLet + 0.6, 76, 70, 1.0); scratch(q3('inside it was') + 0.2, 0.6, 1.0)
lay(qLet, qNot3 - 0.4, (G, D, Em, C), lambda k, t, ch: (cello(t, ch[0] - 12, 3.8, 54, 0.8), arp(t, ch, 50, 0.8)))
for k in range(4): tick(qNot3 + 0.3 + k * 0.5, k % 2 == 0, 1.0)
walk(qWar, qBuy - 0.4, (G, D, Em, C)); clink(q3('a coupon bought') + 0.4, 96, 1.2, -0.4); ching(q3('could be traded') + 0.5, 1.0, 0.4)
clink(qBuy + 0.3, 96, 1.5, -0.5); ching(q3('cash them here') + 0.3, 1.2, 0.5)
hit(q400 + 0.6, 94, 1.2, 43); strings(q400 + 0.6, G, qLeg - q400, 64, 0.9, swell=0.5)
for k, m in enumerate((67, 71, 74, 79, 83, 86)): harp(q3('400 profit') + k * 0.18, m, 72, 1.0)
for m in (43, 55, 62, 67, 71): piano(qLeg + 0.9, m, 4, 62, 0.8)

# ================================================================ 5. one problem
q4 = lambda p: q(4, p)
qNo, qThese, q160, q27, qWait, qOff, q50, qDb, qBk = q4('it could not be done'), q4('these were coupons'), q4('160 million'), q4('27000'), q4('ponzi did not wait'), q4('and he made an offer'), q4('50 interest'), q4('or double your money'), q4('the banks were paying')
drone(V[4] + 0.2, qWait, (28, 40), 42, 0.7); piano(qNo + 0.2, 40, 5, 68, 1.0); piano(q4('not at any size'), 43, 4, 60, 0.8)
for k, t in enumerate(np.arange(grid(qThese), qWait - 0.5, 0.5)): pizz(t, (40, 47, 45, 47)[k % 4], 64, 0.7)
hit(q160 + 0.2, 98, 1.3); strings(q160 + 0.2, (40, 47, 52, 58), q27 - q160, 58, 0.9, prog=TREM, swell=0.5)
clink(q27 + 0.6, 100, 1.6)
stride(qWait, qBk - 0.3, RISE, 0.5, 0.85); murmur(qOff, V[5], 0.2, 0.6)
ching(q50 + 0.4, 1.2); ching(qDb + 0.5, 1.3); tick(qBk + 0.5, True, 1.2); tick(q4('a year'), False, 1.2); piano(q4('a year') + 0.1, 43, 4, 62, 0.8)

# ================================================================ 6. it grows
q5 = lambda p: q(5, p)
qPd, qNext, qMar, qMay, qJun, qJul, qRide, qCop = q5('45 days later'), q5('he paid them with'), q5('by march'), q5('by may'), q5('by june'), q5('by july'), q5('and many of his'), q5('three out of four')
murmur(V[5], V[6], 0.5, 1.4)
walk(V[5] + 0.5, qNext - 0.4, (G, C, D, G), 0.9); coins(V[5] + 1, qPd, 8, 0.8); ching(qPd + 0.6, 1.1); ching(q5('with interest') + 0.3, 1.0)
piano(qNext + 0.2, 40, 5, 66, 0.9); cello(qNext, 28, q5('and those first') - qNext, 58, 0.8)
stride(q5('and those first'), qCop - 0.4, RISE2, 0.6, 1.1)
for at, lv in ((qMar, 0.9), (qMay, 1.1), (qJun, 1.3), (qJul, 1.5)): ching(at + 0.5, lv); hit(at + 0.5, 70 + int(lv * 14), 0.6 + lv * 0.3, 43)
coins(qMar, qRide, 46, 1.0)
lay(qMay, qCop - 0.4, RISE2, lambda k, t, ch: strings(t, ch, 4.3, 50 + 3 * k, 0.7, swell=0.8))
keys(qJul, qRide, 30, 0.8)
hit(qCop + 0.2, 92, 1.1); march(qCop, V[6] - 0.3, 0.3, 0.2, 0.5); strings(qCop + 0.2, G, V[6] - qCop + 0.8, 62, 0.9, swell=0.5)

# ================================================================ 7. the high life
q6 = lambda p: q(6, p)
qCar, qBank, qSame, qSue, qWon, qCheer = q6('he bought a custom'), q6('and he bought control'), q6('the same bank'), q6('when a financial writer'), q6('and won'), q6('when he walked')
stride(V[6] + 0.4, qSame - 0.4, RISE, 1.0, 1.0); lay(V[6] + 0.4, qSame - 0.4, RISE, lambda k, t, ch: horn(t, ch[1], 3.5, 58, 0.7))
horn(qCar + 1.2, 62, 0.25, 80, 1.2); horn(qCar + 1.55, 62, 0.4, 80, 1.2); chuff(qCar + 0.5, qBank - 0.3, 5.0, 7.0, 0.5)
hit(qBank + 0.8, 92, 1.1, 43); ching(qBank + 1.0, 1.3)
piano(qSame + 0.3, 40, 5, 66, 0.9); cello(qSame, 28, qSue - qSame, 58, 0.8)
walk(qSue, qWon - 0.3, (Em, Am, B, Em), 0.9, False); scratch(qSue + 0.8, 0.8, 1.0); gavel(qWon + 0.1, 1.2); gavel(qWon + 0.5, 1.0); ching(q6('half a million') + 0.5, 1.4)
murmur(qCheer - 0.3, V[7], 1.2, 2.2); strings(qCheer, (43, 50, 55, 59, 62, 67), V[7] - qCheer + 0.6, 68, 1.0, swell=0.8)
for k, m in enumerate((67, 71, 74, 79, 83)): harp(qCheer + 0.5 + k * 0.2, m, 70, 0.9)

# ================================================================ 8. the arithmetic
q7 = lambda p: q(7, p)
qEarn, qSay, q15, qMiss, qSo, qHole, qSch, qEnd = q7('he was not earning'), q7('say 100 people'), q7('15000'), q7('the missing 5000'), q7('so to pay them'), q7('the hole got deeper'), q7('a scheme like that'), q7('it ends when')
for k, t in enumerate(np.arange(grid(V[7] + 1), qSo, 1.0)): tick(t, k % 2 == 0, 0.9)
drone(V[7] + 0.3, qSay, (28, 40), 40, 0.6); piano(qEarn + 0.2, 52, 4, 60, 0.8); piano(q7('and every new investor'), 55, 4, 60, 0.8)
for k, t in enumerate(np.arange(grid(qSay), qSo - 0.4, 0.5)): pizz(t, (40, 47, 43, 47)[k % 4], 64, 0.7)
coins(qSay + 0.5, qSay + 3.0, 8, 0.9); ching(q7('he has 10000') + 0.6, 1.0)
hit(q15 + 0.2, 88, 1.0); piano(qMiss + 0.3, 40, 5, 68, 1.0); clink(q7('and now he owes'), 96, 1.2)
for k, t in enumerate(np.arange(qSo, qHole - 0.2, 0.5)):
    lv = 0.5 + 0.6 * (t - qSo) / max(1, qHole - qSo); pizz(t, (40, 47, 43, 47)[k % 4], 72, 0.8 * lv); pizz(t + 0.25, 52 + (0, 3, 7, 3)[k % 4], 66, 0.6 * lv); tick(t, True, lv)
strings(qSo, (40, 47, 52, 58), qHole - qSo + 0.3, 62, 1.0, prog=TREM, swell=4.0)
hit(qHole, 100, 1.4)
for k, m in enumerate((52, 50, 48, 47, 45, 43, 40)): cello(qHole + 0.2 + k * (qSch - qHole - 0.6) / 7, m - 12, 1.6, 66, 1.0)
drone(qSch, qEnd, (28, 40), 40, 0.6); heart(qSch, qEnd, 1.0, 1.0, 0.5, 0.7)
hit(qEnd + 0.9, 102, 1.5); strings(qEnd + 0.9, Em, V[8] - qEnd, 74, 1.0, swell=0.5); motif(qEnd + 1.3, [76, 71, 67, 64], 0.5, 74, 1.0, fn=lambda t, m, v, g: piano(t, m, 4, v, g))

# ================================================================ 9. the Post
q8 = lambda p: q(8, p)
q2d, qBar, qBack, qPaid, q2m, qFew = q8('two days later'), q8('a financial writer named'), q8('the crowd came back'), q8('and ponzi paid them'), q8('2 million'), q8('for a few days')
stride(V[8] + 0.4, q2d - 0.4, RISE, 0.9, 0.9); murmur(V[8], q2d, 0.8, 1.2); scratch(V[8] + 1.2, 0.9, 1.0)
piano(q2d + 0.2, 40, 5, 66, 0.9); drone(q2d, qBack, (28, 40, 47), 44, 0.8); keys(qBar, qBack - 0.4, 34, 0.9); scratch(q8('and printed it') + 0.2, 0.8, 1.3)
for k, t in enumerate(np.arange(grid(qBar), qBack - 0.4, 0.5)): pizz(t, (40, 47, 45, 47)[k % 4], 64, 0.7)
hit(qBack + 0.2, 98, 1.3); murmur(qBack, qFew, 1.6, 2.4); strings(qBack + 0.2, (40, 47, 52, 58), qPaid - qBack, 60, 0.9, prog=TREM, swell=0.5); heart(qBack, qPaid, 0.8, 0.6, 0.6, 0.9)
stride(qPaid + 0.6, qFew - 0.4, (Am, Em, B, Em), 0.8, 0.8)
for k in range(7): ching(q2m + 0.3 + k * 0.7, 1.0, -0.4 + 0.13 * k)
clink(q8('coffee and doughnuts'), 91, 1.0); clink(q8('coffee and doughnuts') + 0.4, 94, 1.0)
murmur(qFew, V[9], 1.2, 0.2); strings(qFew, G, V[9] - qFew + 0.5, 52, 0.8, swell=1.5); harp(q8('the panic stopped') + 0.5, 79, 66, 0.9)

# ================================================================ 10. the fall
q9 = lambda p: q(9, p)
qHd, qAug, qMug, qShut, qTurn, q86 = q9('the headline said'), q9('on august 11'), q9('a mug shot'), q9('that afternoon'), q9('within two days'), q9('he was charged')
drone(V[9] + 0.2, qHd, (28, 40), 44, 0.8); keys(V[9] + 1, qHd - 0.3, 22, 0.7); piano(V[9] + 1.0, 52, 4, 58, 0.8); piano(V[9] + 3.0, 51, 4, 58, 0.8)
hit(qHd + 0.3, 100, 1.4); thud(qHd + 0.3, 1.0, 60); strings(qHd + 0.3, (40, 47, 52, 58), qAug - qHd, 62, 1.0, prog=TREM, swell=0.5); scratch(qHd + 0.9, 0.9, 1.2)
for k, t in enumerate(np.arange(grid(qAug), qMug - 0.3, 0.5)): pizz(t, (40, 46, 45, 46)[k % 4], 66, 0.8)
swish(qMug + 0.1, 1.4, 0.4); clack(qMug + 0.5, 1.4, 700); hit(qMug + 0.5, 104, 1.5); piano(qMug + 0.5, 28, 6, 80, 1.0); strings(qMug + 0.5, Em, qShut - qMug - 0.4, 70, 1.0, swell=0.4)
thud(qShut + 1.6, 1.3, 70); clack(qShut + 1.6, 1.3, 260); murmur(qShut, qTurn, 1.8, 0.6)
for k, m in enumerate((52, 50, 48, 47, 45, 43, 40)): cello(qTurn + k * (q86 - qTurn) / 7, m - 12, 1.8, 64, 1.0)
clack(q9('turned himself in') + 0.8, 1.1, 1100); clack(q9('turned himself in') + 1.0, 1.0, 1300)
gavel(q86 + 0.9, 1.3); gavel(q86 + 1.4, 1.1); gavel(q86 + 1.9, 1.0); hit(q86 + 0.9, 96, 1.2); strings(q86 + 0.9, Em, V[10] - q86 - 0.5, 60, 0.9, swell=0.6)

# ================================================================ 11. the bill
q10 = lambda p: q(10, p)
q6b, q30, qWh = q10('six banks'), q10('the people who trusted'), q10('the whole thing')
lay(V[10] + 0.5, qWh - 0.4, (Am, Em, C, B), lambda k, t, ch: (cello(t, ch[0] - 12, 3.8, 58, 0.9), piano(t, ch[1], 4, 54, 0.8), piano(t + 1.5, ch[2], 4, 50, 0.75), piano(t + 3, ch[3], 4, 50, 0.75)))
hit(q10('20 million') + 0.2, 90, 1.1); hit(q10('more than 300') + 0.4, 96, 1.2)
for k in range(6): thud(q6b + 0.3 + k * 0.4, 0.9 - k * 0.06, 90 - k * 5)
clink(q10('30 cents') + 0.3, 96, 1.4); clink(q10('30 cents') + 0.65, 93, 1.0)
drone(qWh, V[11], (28, 40, 47), 42, 0.7); heart(qWh, V[11] - 0.5, 1.0, 1.0, 0.5, 0.5); clack(q10('handcuffs') + 0.3, 1.0, 1200); piano(q10('about eight months'), 40, 5, 66, 0.9)

# ================================================================ 12. the rest of his life
q11 = lambda p: q(11, p)
qSt, qFl, qDep, qRose, qDied, q75 = q11('then to state prison'), q11('in between'), q11('in 1934'), q11('his wife'), q11('he died'), q11('he left 75')
walk(V[11] + 0.5, qFl - 0.4, (Em, C, Am, B), 0.9, False); clack(V[11] + 2.0, 1.1, 280); thud(V[11] + 2.0, 0.8, 80); clack(qSt + 1.2, 1.1, 280); gavel(q11('a common and notorious') - 0.3, 1.0)
waves(qFl, qDep, 0.8); crickets(q11('and sold swampland'), qDep - 0.3, 1.0); stride(q11('and sold swampland'), qDep - 0.4, RISE, 0.55, 0.55, False); ching(q11('promising 200') + 0.5, 0.9)
for k, m in enumerate((67, 71, 74, 79)): harp(q11('he went to florida') + 0.3 + k * 0.2, m, 66, 0.9)
waves(qDep - 0.3, qRose, 1.1); whistle(qDep + 1.6, 1.8, 0.8); lay(qDep, qRose - 0.4, (Em, C), lambda k, t, ch: bed(k, t, ch, 52, 0.8))
lay(qRose, qDied - 0.4, (Am, Em, C, B), lambda k, t, ch: (cello(t, ch[0] - 12, 3.8, 54, 0.8), piano(t, ch[2] + 12, 4, 54, 0.8), piano(t + 2, ch[3] + 12, 4, 50, 0.75)))
piano(q11('three years later') + 0.6, 40, 5, 64, 0.9)
strings(qDied, (40, 47, 52, 55, 59), V[12] - qDied, 52, 0.9, swell=2.0); motif(qDied + 0.6, [71, 67, 64], 1.2, 60, 0.9, fn=lambda t, m, v, g: piano(t, m, 4, v, g))
for k in range(3): clink(q75 + 0.9 + k * 0.5, 96 - k * 3, 1.3)

# ================================================================ 13. the question
q12 = lambda p: q(12, p)
qBut, qMy, qSoW, qWhere, qSub, qAn, qBat, qCol = q12('but it has carried'), q12('my business was simple'), q12('so when somebody'), q12('where is the money'), q12('subscribe'), q12('animal facts'), q12('historys greatest'), q12('worlds craziest')
lay(V[12] + 0.5, qMy - 0.4, (Em, C, G, D), lambda k, t, ch: (cello(t, ch[0] - 12, 3.8, 58, 0.9), arp(t, ch, 52, 0.85)))
drone(qMy - 0.3, qSoW, (28, 40), 40, 0.6); motif(qMy + 0.3, [64, 67, 71, 67], 1.0, 60, 0.9, fn=lambda t, m, v, g: piano(t, m, 4, v, g)); clink(q12('robbing peter') + 0.3, 96, 1.3, -0.5); clink(q12('to pay paul') + 0.4, 100, 1.3, 0.5)
for k, t in enumerate(np.arange(grid(qSoW), qWhere - 0.3, 0.5)): pizz(t, (40, 47, 43, 47)[k % 4], 66, 0.7)
ching(q12('promises you 50') + 0.4, 1.0)
hit(qWhere + 0.1, 100, 1.4); strings(qWhere + 0.1, (28, 40, 47, 52, 56, 59, 64), qSub - qWhere + 0.4, 66, 1.0, swell=1.2)       # E major
for k, m in enumerate((64, 68, 71, 76, 80, 83)): harp(qWhere + 1.2 + k * 0.22, m, 68, 0.9)
e0 = qSub
hit(e0, 92, 1.2); strings(e0, (40, 47, 52, 56, 59, 64), DUR - e0 - 0.5, 70, 1.0, swell=0.8)
for k, (t, m) in enumerate(zip(np.arange(e0 + 0.5, DUR - 5.5, 1.0), [64, 71, 69, 68, 64, 71, 73, 71, 68, 69, 71, 76] * 3)): harp(t, m + 12, 70, 0.9); piano(t, m, 3.5, 52, 0.6)
for k, t in enumerate(np.arange(grid(e0 + 0.5), DUR - 6, 0.5)): pizz(t, (40, 47)[k % 2], 64, 0.6)
for at, m in ((qAn, 76), (qBat, 80), (qCol, 83)): harp(at, m, 76, 1.0); harp(at + 0.12, m + 7, 70, 0.8)
tend = DUR - 5.2
for k, m in enumerate((40, 52, 59, 64, 68, 71, 76)): piano(tend + k * 0.16, m, 6, 68, 1.0)
low.add(tend, inst(TIMP, 40, 4, 80), 1.0)

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
